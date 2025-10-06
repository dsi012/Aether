/*
** cFS MCP Interface Application Header File
**
** This application provides MCP (Model Context Protocol) interface for cFS,
** allowing AI agents to interact with the Core Flight System.
**
** Designed for onboard spacecraft deployment with astronaut interaction.
*/

#ifndef MCP_INTERFACE_APP_H
#define MCP_INTERFACE_APP_H

/*
** Required header files
*/
#include "cfe.h"
#include "cfe_error.h"
#include "cfe_evs.h"
#include "cfe_sb.h"
#include "cfe_es.h"

#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>

/*
** Application constants
*/
#define MCP_INTERFACE_APP_NAME                "MCP_INTERFACE"
#define MCP_INTERFACE_APP_PIPE_DEPTH          32
#define MCP_INTERFACE_APP_PIPE_NAME           "MCP_INTERFACE_CMD_PIPE"

#define MCP_INTERFACE_SOCKET_PATH             "/tmp/cfs_mcp.sock"
#define MCP_MAX_JSON_SIZE                     4096
#define MCP_MAX_CLIENTS                       4
#define MCP_MAX_APP_NAME_LEN                  20
#define MCP_MAX_CMD_NAME_LEN                  32

/*
** Event message IDs
*/
#define MCP_INTERFACE_STARTUP_INF_EID         1
#define MCP_INTERFACE_COMMAND_ERR_EID         2
#define MCP_INTERFACE_SOCKET_ERR_EID          3
#define MCP_INTERFACE_CLIENT_CONNECT_INF_EID  4
#define MCP_INTERFACE_CLIENT_DISCONNECT_INF_EID 5
#define MCP_INTERFACE_COMMAND_SUCCESS_INF_EID 6
#define MCP_INTERFACE_TELEMETRY_INF_EID       7
#define MCP_INTERFACE_SAFETY_ERR_EID          8

/*
** Command Codes
*/
#define MCP_INTERFACE_NOOP_CC                 0
#define MCP_INTERFACE_RESET_COUNTERS_CC       1
#define MCP_INTERFACE_ENABLE_DEBUG_CC         2
#define MCP_INTERFACE_DISABLE_DEBUG_CC        3

/*
** MCP Command Types
*/
typedef enum {
    MCP_CMD_SEND_COMMAND = 0,
    MCP_CMD_GET_TELEMETRY,
    MCP_CMD_GET_SYSTEM_STATUS,
    MCP_CMD_MANAGE_APP,
    MCP_CMD_GET_FILE_LIST,
    MCP_CMD_READ_FILE,
    MCP_CMD_WRITE_FILE,
    MCP_CMD_GET_EVENT_LOG,
    MCP_CMD_EMERGENCY_STOP,
    MCP_CMD_MAX
} MCP_CommandType_t;

/*
** MCP Request/Response structures
*/
typedef struct {
    uint32 id;
    MCP_CommandType_t type;
    char app_name[MCP_MAX_APP_NAME_LEN];
    char command[MCP_MAX_CMD_NAME_LEN];
    char params[MCP_MAX_JSON_SIZE];
    boolean require_confirmation;
    boolean is_critical;
} MCP_Request_t;

typedef struct {
    uint32 id;
    int32 status;
    char result[MCP_MAX_JSON_SIZE];
    char error_msg[256];
    uint32 timestamp;
} MCP_Response_t;

/*
** Application data structure
*/
typedef struct {
    /*
    ** Command interface counters
    */
    uint8 CmdCounter;
    uint8 ErrCounter;

    /*
    ** Housekeeping telemetry packet
    */
    CFE_SB_TlmHdr_t HkTlm;

    /*
    ** Run Status variable used in the main processing loop
    */
    uint32 RunStatus;

    /*
    ** Operational data (not reported in housekeeping)
    */
    CFE_SB_PipeId_t CommandPipe;

    /*
    ** MCP Server data
    */
    int32 ServerSocket;
    int32 ClientSockets[MCP_MAX_CLIENTS];
    uint32 ActiveClients;
    boolean DebugMode;
    uint32 RequestCounter;
    uint32 SuccessCounter;
    uint32 ErrorCounter;
    
    /*
    ** Safety features
    */
    boolean SafetyMode;
    uint32 CriticalCommandCount;
    uint32 LastCriticalCommandTime;

} MCP_INTERFACE_AppData_t;

/*
** Application global data
*/
extern MCP_INTERFACE_AppData_t MCP_INTERFACE_AppData;

/*
** Function Prototypes
*/
void MCP_INTERFACE_AppMain(void);
int32 MCP_INTERFACE_AppInit(void);
void MCP_INTERFACE_ProcessCommandPacket(void);
void MCP_INTERFACE_ProcessGroundCommand(void);
void MCP_INTERFACE_ReportHousekeeping(void);
void MCP_INTERFACE_ResetCounters(void);
boolean MCP_INTERFACE_VerifyCmdLength(CFE_SB_MsgPtr_t msg, uint16 ExpectedLength);

/*
** MCP Server Functions
*/
int32 MCP_INTERFACE_InitSocket(void);
void MCP_INTERFACE_ProcessMCPClients(void);
int32 MCP_INTERFACE_HandleMCPRequest(int32 client_socket, MCP_Request_t *request);
int32 MCP_INTERFACE_SendMCPResponse(int32 client_socket, MCP_Response_t *response);

/*
** MCP Command Handlers
*/
int32 MCP_INTERFACE_HandleSendCommand(MCP_Request_t *request, MCP_Response_t *response);
int32 MCP_INTERFACE_HandleGetTelemetry(MCP_Request_t *request, MCP_Response_t *response);
int32 MCP_INTERFACE_HandleGetSystemStatus(MCP_Request_t *request, MCP_Response_t *response);
int32 MCP_INTERFACE_HandleManageApp(MCP_Request_t *request, MCP_Response_t *response);
int32 MCP_INTERFACE_HandleGetFileList(MCP_Request_t *request, MCP_Response_t *response);
int32 MCP_INTERFACE_HandleReadFile(MCP_Request_t *request, MCP_Response_t *response);
int32 MCP_INTERFACE_HandleWriteFile(MCP_Request_t *request, MCP_Response_t *response);
int32 MCP_INTERFACE_HandleGetEventLog(MCP_Request_t *request, MCP_Response_t *response);
int32 MCP_INTERFACE_HandleEmergencyStop(MCP_Request_t *request, MCP_Response_t *response);

/*
** Safety and utility functions
*/
boolean MCP_INTERFACE_IsSafeCommand(MCP_Request_t *request);
boolean MCP_INTERFACE_RequiresConfirmation(MCP_Request_t *request);
int32 MCP_INTERFACE_ValidateRequest(MCP_Request_t *request);
void MCP_INTERFACE_LogSafetyEvent(const char *event_msg, uint32 event_id);

/*
** JSON utility functions
*/
int32 MCP_INTERFACE_ParseJSONRequest(const char *json_str, MCP_Request_t *request);
int32 MCP_INTERFACE_FormatJSONResponse(MCP_Response_t *response, char *json_str, uint32 max_len);

#endif /* MCP_INTERFACE_APP_H */
