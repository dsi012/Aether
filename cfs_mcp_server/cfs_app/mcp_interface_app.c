/*
** cFS MCP Interface Application Implementation
**
** This application provides MCP (Model Context Protocol) interface for cFS,
** allowing AI agents to interact with the Core Flight System.
**
** Designed for onboard spacecraft deployment with astronaut interaction.
*/

/*
** Include Files
*/
#include "mcp_interface_app.h"

/*
** Global Data
*/
MCP_INTERFACE_AppData_t MCP_INTERFACE_AppData;

/*
** Application entry point and main process loop
*/
void MCP_INTERFACE_AppMain(void)
{
    int32 status;
    uint32 RunStatus = CFE_ES_APP_RUN;

    CFE_ES_PerfLogEntry(MCP_INTERFACE_APP_PERF_ID);

    status = MCP_INTERFACE_AppInit();
    if (status != CFE_SUCCESS)
    {
        MCP_INTERFACE_AppData.RunStatus = CFE_ES_APP_ERROR;
    }

    /*
    ** Main process loop
    */
    while (CFE_ES_RunLoop(&RunStatus) == TRUE)
    {
        CFE_ES_PerfLogExit(MCP_INTERFACE_APP_PERF_ID);

        /* Pend on receipt of command packet */
        status = CFE_SB_RcvMsg(&MCP_INTERFACE_AppData.MsgPtr,
                               MCP_INTERFACE_AppData.CommandPipe,
                               50); /* 50ms timeout for responsiveness */

        CFE_ES_PerfLogEntry(MCP_INTERFACE_APP_PERF_ID);

        if (status == CFE_SUCCESS)
        {
            MCP_INTERFACE_ProcessCommandPacket();
        }
        else if (status == CFE_SB_TIME_OUT)
        {
            /* Timeout - process MCP clients */
            MCP_INTERFACE_ProcessMCPClients();
        }
        else
        {
            CFE_EVS_SendEvent(MCP_INTERFACE_COMMAND_ERR_EID,
                            CFE_EVS_ERROR,
                            "MCP_INTERFACE: SB receive error = 0x%08X", status);
        }
    }

    CFE_ES_ExitApp(RunStatus);

} /* End of MCP_INTERFACE_AppMain() */

/*
** Application initialization
*/
int32 MCP_INTERFACE_AppInit(void)
{
    int32 status;

    MCP_INTERFACE_AppData.RunStatus = CFE_ES_APP_RUN;

    /*
    ** Initialize app command execution counters
    */
    MCP_INTERFACE_AppData.CmdCounter = 0;
    MCP_INTERFACE_AppData.ErrCounter = 0;

    /*
    ** Initialize app configuration data
    */
    MCP_INTERFACE_AppData.ActiveClients = 0;
    MCP_INTERFACE_AppData.DebugMode = FALSE;
    MCP_INTERFACE_AppData.RequestCounter = 0;
    MCP_INTERFACE_AppData.SuccessCounter = 0;
    MCP_INTERFACE_AppData.ErrorCounter = 0;
    MCP_INTERFACE_AppData.SafetyMode = TRUE; /* Default to safe mode */
    MCP_INTERFACE_AppData.CriticalCommandCount = 0;
    MCP_INTERFACE_AppData.LastCriticalCommandTime = 0;

    /*
    ** Initialize event filter table
    */
    /* No filters initially */

    /*
    ** Register the app with Executive services
    */
    CFE_ES_RegisterApp();

    /*
    ** Register the events
    */
    status = CFE_EVS_Register(NULL,
                             0,
                             CFE_EVS_BINARY_FILTER);

    if (status != CFE_SUCCESS)
    {
        CFE_ES_WriteToSysLog("MCP_INTERFACE: Error Registering Events, RC = 0x%08X\n",
                           status);
        return (status);
    }

    /*
    ** Initialize housekeeping packet (clear user data area).
    */
    CFE_SB_InitMsg(&MCP_INTERFACE_AppData.HkTlm,
                   MCP_INTERFACE_HK_TLM_MID,
                   sizeof(MCP_INTERFACE_AppData.HkTlm), TRUE);

    /*
    ** Create Software Bus message pipe.
    */
    status = CFE_SB_CreatePipe(&MCP_INTERFACE_AppData.CommandPipe,
                              MCP_INTERFACE_APP_PIPE_DEPTH,
                              MCP_INTERFACE_APP_PIPE_NAME);
    if (status != CFE_SUCCESS)
    {
        CFE_ES_WriteToSysLog("MCP_INTERFACE: Error creating pipe, RC = 0x%08X\n",
                           status);
        return (status);
    }

    /*
    ** Subscribe to Housekeeping request commands
    */
    status = CFE_SB_Subscribe(MCP_INTERFACE_HK_REQ_MID,
                             MCP_INTERFACE_AppData.CommandPipe);
    if (status != CFE_SUCCESS)
    {
        CFE_ES_WriteToSysLog("MCP_INTERFACE: Error Subscribing to HK request, RC = 0x%08X\n",
                           status);
        return (status);
    }

    /*
    ** Subscribe to ground command packets
    */
    status = CFE_SB_Subscribe(MCP_INTERFACE_CMD_MID,
                             MCP_INTERFACE_AppData.CommandPipe);
    if (status != CFE_SUCCESS)
    {
        CFE_ES_WriteToSysLog("MCP_INTERFACE: Error Subscribing to Commands, RC = 0x%08X\n",
                           status);
        return (status);
    }

    /*
    ** Initialize MCP socket server
    */
    status = MCP_INTERFACE_InitSocket();
    if (status != CFE_SUCCESS)
    {
        CFE_EVS_SendEvent(MCP_INTERFACE_SOCKET_ERR_EID,
                        CFE_EVS_ERROR,
                        "MCP_INTERFACE: Failed to initialize socket server, RC = 0x%08X", status);
        return (status);
    }

    CFE_EVS_SendEvent(MCP_INTERFACE_STARTUP_INF_EID,
                     CFE_EVS_INFORMATION,
                     "MCP_INTERFACE App Initialized. Version %d.%d.%d.%d",
                     MCP_INTERFACE_MAJOR_VERSION,
                     MCP_INTERFACE_MINOR_VERSION,
                     MCP_INTERFACE_REVISION,
                     MCP_INTERFACE_MISSION_REV);

    return (CFE_SUCCESS);

} /* End of MCP_INTERFACE_AppInit() */

/*
** Process command packets
*/
void MCP_INTERFACE_ProcessCommandPacket(void)
{
    CFE_SB_MsgId_t MsgId;

    MsgId = CFE_SB_GetMsgId(MCP_INTERFACE_AppData.MsgPtr);

    switch (MsgId)
    {
        case MCP_INTERFACE_HK_REQ_MID:
            MCP_INTERFACE_ReportHousekeeping();
            break;

        case MCP_INTERFACE_CMD_MID:
            MCP_INTERFACE_ProcessGroundCommand();
            break;

        default:
            CFE_EVS_SendEvent(MCP_INTERFACE_COMMAND_ERR_EID,
                            CFE_EVS_ERROR,
                            "MCP_INTERFACE: invalid command packet,MID = 0x%x",
                            MsgId);
            break;
    }

    return;

} /* End MCP_INTERFACE_ProcessCommandPacket */

/*
** Process ground commands
*/
void MCP_INTERFACE_ProcessGroundCommand(void)
{
    uint16 CommandCode;

    CommandCode = CFE_SB_GetCmdCode(MCP_INTERFACE_AppData.MsgPtr);

    /* Process "known" commands */
    switch (CommandCode)
    {
        case MCP_INTERFACE_NOOP_CC:
            if (MCP_INTERFACE_VerifyCmdLength(MCP_INTERFACE_AppData.MsgPtr,
                                            sizeof(MCP_INTERFACE_NoopCmd_t)))
            {
                MCP_INTERFACE_AppData.CmdCounter++;

                CFE_EVS_SendEvent(MCP_INTERFACE_COMMAND_SUCCESS_INF_EID,
                                CFE_EVS_INFORMATION,
                                "MCP_INTERFACE: NOOP command");
            }
            break;

        case MCP_INTERFACE_RESET_COUNTERS_CC:
            if (MCP_INTERFACE_VerifyCmdLength(MCP_INTERFACE_AppData.MsgPtr,
                                            sizeof(MCP_INTERFACE_ResetCmd_t)))
            {
                MCP_INTERFACE_ResetCounters();
            }
            break;

        case MCP_INTERFACE_ENABLE_DEBUG_CC:
            if (MCP_INTERFACE_VerifyCmdLength(MCP_INTERFACE_AppData.MsgPtr,
                                            sizeof(MCP_INTERFACE_DebugCmd_t)))
            {
                MCP_INTERFACE_AppData.DebugMode = TRUE;
                MCP_INTERFACE_AppData.CmdCounter++;

                CFE_EVS_SendEvent(MCP_INTERFACE_COMMAND_SUCCESS_INF_EID,
                                CFE_EVS_INFORMATION,
                                "MCP_INTERFACE: Debug mode enabled");
            }
            break;

        case MCP_INTERFACE_DISABLE_DEBUG_CC:
            if (MCP_INTERFACE_VerifyCmdLength(MCP_INTERFACE_AppData.MsgPtr,
                                            sizeof(MCP_INTERFACE_DebugCmd_t)))
            {
                MCP_INTERFACE_AppData.DebugMode = FALSE;
                MCP_INTERFACE_AppData.CmdCounter++;

                CFE_EVS_SendEvent(MCP_INTERFACE_COMMAND_SUCCESS_INF_EID,
                                CFE_EVS_INFORMATION,
                                "MCP_INTERFACE: Debug mode disabled");
            }
            break;

        /* default case already found during FC vs length test */
        default:
            CFE_EVS_SendEvent(MCP_INTERFACE_COMMAND_ERR_EID,
                            CFE_EVS_ERROR,
                            "MCP_INTERFACE: Invalid ground command code: CC = %d",
                            CommandCode);
            MCP_INTERFACE_AppData.ErrCounter++;
            break;
    }

    return;

} /* End of MCP_INTERFACE_ProcessGroundCommand() */

/*
** Initialize Unix Domain Socket for MCP communication
*/
int32 MCP_INTERFACE_InitSocket(void)
{
    struct sockaddr_un server_addr;
    int32 result;
    int32 i;

    /* Initialize client sockets array */
    for (i = 0; i < MCP_MAX_CLIENTS; i++)
    {
        MCP_INTERFACE_AppData.ClientSockets[i] = -1;
    }

    /* Create socket */
    MCP_INTERFACE_AppData.ServerSocket = socket(AF_UNIX, SOCK_STREAM, 0);
    if (MCP_INTERFACE_AppData.ServerSocket < 0)
    {
        CFE_ES_WriteToSysLog("MCP_INTERFACE: Failed to create socket\n");
        return CFE_ES_ERR_APP_CREATE;
    }

    /* Remove any existing socket file */
    unlink(MCP_INTERFACE_SOCKET_PATH);

    /* Set up server address */
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sun_family = AF_UNIX;
    strncpy(server_addr.sun_path, MCP_INTERFACE_SOCKET_PATH, 
            sizeof(server_addr.sun_path) - 1);

    /* Bind socket */
    result = bind(MCP_INTERFACE_AppData.ServerSocket,
                 (struct sockaddr *)&server_addr,
                 sizeof(server_addr));
    if (result < 0)
    {
        CFE_ES_WriteToSysLog("MCP_INTERFACE: Failed to bind socket\n");
        close(MCP_INTERFACE_AppData.ServerSocket);
        return CFE_ES_ERR_APP_CREATE;
    }

    /* Listen for connections */
    result = listen(MCP_INTERFACE_AppData.ServerSocket, MCP_MAX_CLIENTS);
    if (result < 0)
    {
        CFE_ES_WriteToSysLog("MCP_INTERFACE: Failed to listen on socket\n");
        close(MCP_INTERFACE_AppData.ServerSocket);
        unlink(MCP_INTERFACE_SOCKET_PATH);
        return CFE_ES_ERR_APP_CREATE;
    }

    /* Set socket to non-blocking */
    fcntl(MCP_INTERFACE_AppData.ServerSocket, F_SETFL, O_NONBLOCK);

    CFE_EVS_SendEvent(MCP_INTERFACE_STARTUP_INF_EID,
                     CFE_EVS_INFORMATION,
                     "MCP_INTERFACE: Socket server initialized at %s",
                     MCP_INTERFACE_SOCKET_PATH);

    return CFE_SUCCESS;

} /* End MCP_INTERFACE_InitSocket */

/*
** Process MCP client connections and requests
*/
void MCP_INTERFACE_ProcessMCPClients(void)
{
    int32 new_client;
    int32 i;
    struct sockaddr_un client_addr;
    socklen_t client_len = sizeof(client_addr);
    char buffer[MCP_MAX_JSON_SIZE];
    ssize_t bytes_received;
    MCP_Request_t request;
    MCP_Response_t response;

    /* Accept new connections */
    new_client = accept(MCP_INTERFACE_AppData.ServerSocket,
                       (struct sockaddr *)&client_addr,
                       &client_len);
    
    if (new_client >= 0)
    {
        /* Find empty slot for new client */
        for (i = 0; i < MCP_MAX_CLIENTS; i++)
        {
            if (MCP_INTERFACE_AppData.ClientSockets[i] == -1)
            {
                MCP_INTERFACE_AppData.ClientSockets[i] = new_client;
                MCP_INTERFACE_AppData.ActiveClients++;
                
                CFE_EVS_SendEvent(MCP_INTERFACE_CLIENT_CONNECT_INF_EID,
                                CFE_EVS_INFORMATION,
                                "MCP_INTERFACE: New client connected (slot %d)", i);
                break;
            }
        }
        
        if (i >= MCP_MAX_CLIENTS)
        {
            /* No available slots - reject connection */
            close(new_client);
            CFE_EVS_SendEvent(MCP_INTERFACE_COMMAND_ERR_EID,
                            CFE_EVS_ERROR,
                            "MCP_INTERFACE: Maximum clients reached, connection rejected");
        }
    }

    /* Process existing client requests */
    for (i = 0; i < MCP_MAX_CLIENTS; i++)
    {
        if (MCP_INTERFACE_AppData.ClientSockets[i] != -1)
        {
            bytes_received = recv(MCP_INTERFACE_AppData.ClientSockets[i],
                                buffer, sizeof(buffer) - 1, MSG_DONTWAIT);
            
            if (bytes_received > 0)
            {
                buffer[bytes_received] = '\0';
                
                /* Parse JSON request */
                if (MCP_INTERFACE_ParseJSONRequest(buffer, &request) == CFE_SUCCESS)
                {
                    /* Handle the request */
                    MCP_INTERFACE_HandleMCPRequest(MCP_INTERFACE_AppData.ClientSockets[i], &request);
                }
                else
                {
                    /* Send error response for invalid JSON */
                    memset(&response, 0, sizeof(response));
                    response.id = 0;
                    response.status = -1;
                    strncpy(response.error_msg, "Invalid JSON request", sizeof(response.error_msg) - 1);
                    MCP_INTERFACE_SendMCPResponse(MCP_INTERFACE_AppData.ClientSockets[i], &response);
                }
            }
            else if (bytes_received == 0 || (bytes_received < 0 && errno != EAGAIN && errno != EWOULDBLOCK))
            {
                /* Client disconnected or error */
                close(MCP_INTERFACE_AppData.ClientSockets[i]);
                MCP_INTERFACE_AppData.ClientSockets[i] = -1;
                MCP_INTERFACE_AppData.ActiveClients--;
                
                CFE_EVS_SendEvent(MCP_INTERFACE_CLIENT_DISCONNECT_INF_EID,
                                CFE_EVS_INFORMATION,
                                "MCP_INTERFACE: Client disconnected (slot %d)", i);
            }
        }
    }

} /* End MCP_INTERFACE_ProcessMCPClients */

/*
** Handle MCP request
*/
int32 MCP_INTERFACE_HandleMCPRequest(int32 client_socket, MCP_Request_t *request)
{
    MCP_Response_t response;
    int32 result = CFE_SUCCESS;

    /* Initialize response */
    memset(&response, 0, sizeof(response));
    response.id = request->id;
    response.timestamp = CFE_TIME_GetTime().Seconds;

    /* Validate request */
    if (MCP_INTERFACE_ValidateRequest(request) != CFE_SUCCESS)
    {
        response.status = -1;
        strncpy(response.error_msg, "Invalid request parameters", sizeof(response.error_msg) - 1);
        MCP_INTERFACE_AppData.ErrorCounter++;
        return MCP_INTERFACE_SendMCPResponse(client_socket, &response);
    }

    /* Safety checks */
    if (!MCP_INTERFACE_IsSafeCommand(request))
    {
        response.status = -1;
        strncpy(response.error_msg, "Command blocked by safety system", sizeof(response.error_msg) - 1);
        MCP_INTERFACE_LogSafetyEvent("Unsafe command blocked", MCP_INTERFACE_SAFETY_ERR_EID);
        MCP_INTERFACE_AppData.ErrorCounter++;
        return MCP_INTERFACE_SendMCPResponse(client_socket, &response);
    }

    /* Process request based on type */
    switch (request->type)
    {
        case MCP_CMD_SEND_COMMAND:
            result = MCP_INTERFACE_HandleSendCommand(request, &response);
            break;

        case MCP_CMD_GET_TELEMETRY:
            result = MCP_INTERFACE_HandleGetTelemetry(request, &response);
            break;

        case MCP_CMD_GET_SYSTEM_STATUS:
            result = MCP_INTERFACE_HandleGetSystemStatus(request, &response);
            break;

        case MCP_CMD_MANAGE_APP:
            result = MCP_INTERFACE_HandleManageApp(request, &response);
            break;

        case MCP_CMD_GET_FILE_LIST:
            result = MCP_INTERFACE_HandleGetFileList(request, &response);
            break;

        case MCP_CMD_READ_FILE:
            result = MCP_INTERFACE_HandleReadFile(request, &response);
            break;

        case MCP_CMD_WRITE_FILE:
            result = MCP_INTERFACE_HandleWriteFile(request, &response);
            break;

        case MCP_CMD_GET_EVENT_LOG:
            result = MCP_INTERFACE_HandleGetEventLog(request, &response);
            break;

        case MCP_CMD_EMERGENCY_STOP:
            result = MCP_INTERFACE_HandleEmergencyStop(request, &response);
            break;

        default:
            response.status = -1;
            snprintf(response.error_msg, sizeof(response.error_msg), 
                    "Unknown command type: %d", request->type);
            result = CFE_ES_ERR_APPNAME;
            break;
    }

    /* Update counters */
    MCP_INTERFACE_AppData.RequestCounter++;
    if (result == CFE_SUCCESS && response.status == 0)
    {
        MCP_INTERFACE_AppData.SuccessCounter++;
    }
    else
    {
        MCP_INTERFACE_AppData.ErrorCounter++;
    }

    /* Send response */
    return MCP_INTERFACE_SendMCPResponse(client_socket, &response);

} /* End MCP_INTERFACE_HandleMCPRequest */

/*
** Report housekeeping telemetry
*/
void MCP_INTERFACE_ReportHousekeeping(void)
{
    /* Update telemetry data */
    MCP_INTERFACE_AppData.HkTlm.CmdCounter = MCP_INTERFACE_AppData.CmdCounter;
    MCP_INTERFACE_AppData.HkTlm.ErrCounter = MCP_INTERFACE_AppData.ErrCounter;
    MCP_INTERFACE_AppData.HkTlm.ActiveClients = MCP_INTERFACE_AppData.ActiveClients;
    MCP_INTERFACE_AppData.HkTlm.RequestCounter = MCP_INTERFACE_AppData.RequestCounter;
    MCP_INTERFACE_AppData.HkTlm.SuccessCounter = MCP_INTERFACE_AppData.SuccessCounter;
    MCP_INTERFACE_AppData.HkTlm.ErrorCounter = MCP_INTERFACE_AppData.ErrorCounter;

    CFE_SB_TimeStampMsg((CFE_SB_Msg_t *) &MCP_INTERFACE_AppData.HkTlm);
    CFE_SB_SendMsg((CFE_SB_Msg_t *) &MCP_INTERFACE_AppData.HkTlm);

} /* End of MCP_INTERFACE_ReportHousekeeping() */

/*
** Reset counters
*/
void MCP_INTERFACE_ResetCounters(void)
{
    MCP_INTERFACE_AppData.CmdCounter = 0;
    MCP_INTERFACE_AppData.ErrCounter = 0;
    MCP_INTERFACE_AppData.RequestCounter = 0;
    MCP_INTERFACE_AppData.SuccessCounter = 0;
    MCP_INTERFACE_AppData.ErrorCounter = 0;

    CFE_EVS_SendEvent(MCP_INTERFACE_COMMAND_SUCCESS_INF_EID,
                     CFE_EVS_INFORMATION,
                     "MCP_INTERFACE: Counters reset");

} /* End of MCP_INTERFACE_ResetCounters() */

/*
** Verify command packet length
*/
boolean MCP_INTERFACE_VerifyCmdLength(CFE_SB_MsgPtr_t msg, uint16 ExpectedLength)
{
    boolean result = TRUE;

    uint16 ActualLength = CFE_SB_GetTotalMsgLength(msg);

    if (ExpectedLength != ActualLength)
    {
        CFE_SB_MsgId_t MessageID = CFE_SB_GetMsgId(msg);
        uint16 CommandCode = CFE_SB_GetCmdCode(msg);

        CFE_EVS_SendEvent(MCP_INTERFACE_COMMAND_ERR_EID,
                         CFE_EVS_ERROR,
                         "MCP_INTERFACE: Invalid msg length: ID = 0x%X,  CC = %d, Len = %d, Expected = %d",
                         MessageID, CommandCode, ActualLength, ExpectedLength);
        result = FALSE;
        MCP_INTERFACE_AppData.ErrCounter++;
    }

    return (result);

} /* End of MCP_INTERFACE_VerifyCmdLength() */
