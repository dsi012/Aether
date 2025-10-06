/*
** MCP Interface Command Handlers
**
** This file contains the implementation of MCP command handlers
** for the cFS MCP Interface Application.
*/

/*
** Include Files
*/
#include "mcp_interface_app.h"
#include <stdio.h>
#include <stdlib.h>
#include <dirent.h>
#include <sys/stat.h>

/*
** Handle Send Command request
*/
int32 MCP_INTERFACE_HandleSendCommand(MCP_Request_t *request, MCP_Response_t *response)
{
    CFE_SB_Msg_t *cmd_msg;
    CFE_SB_MsgId_t msg_id;
    uint16 cmd_code;
    int32 status;
    char result_str[512];

    /* Validate app name */
    if (strlen(request->app_name) == 0)
    {
        response->status = -1;
        strncpy(response->error_msg, "App name is required", sizeof(response->error_msg) - 1);
        return CFE_ES_ERR_APPNAME;
    }

    /* Critical command handling */
    if (request->is_critical)
    {
        uint32 current_time = CFE_TIME_GetTime().Seconds;
        
        /* Rate limiting for critical commands */
        if (current_time - MCP_INTERFACE_AppData.LastCriticalCommandTime < 5)
        {
            response->status = -1;
            strncpy(response->error_msg, "Critical command rate limit exceeded", sizeof(response->error_msg) - 1);
            return CFE_ES_ERR_APPNAME;
        }
        
        MCP_INTERFACE_AppData.CriticalCommandCount++;
        MCP_INTERFACE_AppData.LastCriticalCommandTime = current_time;
        
        /* Log critical command */
        CFE_EVS_SendEvent(MCP_INTERFACE_COMMAND_SUCCESS_INF_EID,
                         CFE_EVS_INFORMATION,
                         "MCP_INTERFACE: Critical command sent to %s: %s",
                         request->app_name, request->command);
    }

    /* Simple command mapping - in real implementation, this would be more sophisticated */
    if (strcmp(request->app_name, "CFE_ES") == 0)
    {
        msg_id = CFE_ES_CMD_MID;
        if (strcmp(request->command, "NOOP") == 0)
        {
            cmd_code = CFE_ES_NOOP_CC;
        }
        else if (strcmp(request->command, "RESET_COUNTERS") == 0)
        {
            cmd_code = CFE_ES_RESET_COUNTERS_CC;
        }
        else
        {
            response->status = -1;
            snprintf(response->error_msg, sizeof(response->error_msg),
                    "Unknown command '%s' for app '%s'", request->command, request->app_name);
            return CFE_ES_ERR_APPNAME;
        }
    }
    else if (strcmp(request->app_name, "FM") == 0)
    {
        msg_id = FM_CMD_MID;
        if (strcmp(request->command, "GET_DIR_LIST") == 0)
        {
            cmd_code = FM_GET_DIR_LIST_CC;
        }
        else
        {
            response->status = -1;
            snprintf(response->error_msg, sizeof(response->error_msg),
                    "Unknown command '%s' for app '%s'", request->command, request->app_name);
            return CFE_ES_ERR_APPNAME;
        }
    }
    else
    {
        response->status = -1;
        snprintf(response->error_msg, sizeof(response->error_msg),
                "Unknown app '%s'", request->app_name);
        return CFE_ES_ERR_APPNAME;
    }

    /* Create and send command */
    cmd_msg = CFE_SB_CreateMsg(msg_id, sizeof(CFE_SB_CmdHdr_t), TRUE);
    if (cmd_msg != NULL)
    {
        CFE_SB_SetCmdCode(cmd_msg, cmd_code);
        status = CFE_SB_SendMsg(cmd_msg);
        
        if (status == CFE_SUCCESS)
        {
            response->status = 0;
            snprintf(result_str, sizeof(result_str),
                    "{\"command_sent\": true, \"app\": \"%s\", \"command\": \"%s\", \"msg_id\": \"0x%04X\", \"cmd_code\": %d}",
                    request->app_name, request->command, msg_id, cmd_code);
            strncpy(response->result, result_str, sizeof(response->result) - 1);
        }
        else
        {
            response->status = -1;
            snprintf(response->error_msg, sizeof(response->error_msg),
                    "Failed to send command, status = 0x%08X", status);
        }
    }
    else
    {
        response->status = -1;
        strncpy(response->error_msg, "Failed to create command message", sizeof(response->error_msg) - 1);
    }

    return CFE_SUCCESS;

} /* End MCP_INTERFACE_HandleSendCommand */

/*
** Handle Get Telemetry request
*/
int32 MCP_INTERFACE_HandleGetTelemetry(MCP_Request_t *request, MCP_Response_t *response)
{
    char result_str[2048];
    uint32 current_time;

    /* Get current system time */
    current_time = CFE_TIME_GetTime().Seconds;

    /* For demonstration, return MCP interface app's own telemetry */
    if (strcmp(request->app_name, "MCP_INTERFACE") == 0)
    {
        snprintf(result_str, sizeof(result_str),
                "{"
                "\"app_name\": \"MCP_INTERFACE\","
                "\"timestamp\": %u,"
                "\"cmd_counter\": %u,"
                "\"err_counter\": %u,"
                "\"active_clients\": %u,"
                "\"request_counter\": %u,"
                "\"success_counter\": %u,"
                "\"error_counter\": %u,"
                "\"safety_mode\": %s,"
                "\"debug_mode\": %s"
                "}",
                current_time,
                MCP_INTERFACE_AppData.CmdCounter,
                MCP_INTERFACE_AppData.ErrCounter,
                MCP_INTERFACE_AppData.ActiveClients,
                MCP_INTERFACE_AppData.RequestCounter,
                MCP_INTERFACE_AppData.SuccessCounter,
                MCP_INTERFACE_AppData.ErrorCounter,
                MCP_INTERFACE_AppData.SafetyMode ? "true" : "false",
                MCP_INTERFACE_AppData.DebugMode ? "true" : "false");
    }
    else
    {
        /* In a real implementation, this would query the actual app's telemetry */
        snprintf(result_str, sizeof(result_str),
                "{"
                "\"app_name\": \"%s\","
                "\"timestamp\": %u,"
                "\"status\": \"telemetry_not_available\","
                "\"message\": \"Telemetry retrieval for %s not implemented yet\""
                "}",
                request->app_name, current_time, request->app_name);
    }

    response->status = 0;
    strncpy(response->result, result_str, sizeof(response->result) - 1);

    return CFE_SUCCESS;

} /* End MCP_INTERFACE_HandleGetTelemetry */

/*
** Handle Get System Status request
*/
int32 MCP_INTERFACE_HandleGetSystemStatus(MCP_Request_t *request, MCP_Response_t *response)
{
    char result_str[3072];
    uint32 current_time;
    CFE_ES_AppInfo_t app_info;
    int32 status;

    current_time = CFE_TIME_GetTime().Seconds;

    /* Get Executive Services information */
    status = CFE_ES_GetAppInfo(&app_info, "MCP_INTERFACE");
    
    snprintf(result_str, sizeof(result_str),
            "{"
            "\"system_status\": {"
            "\"timestamp\": %u,"
            "\"cfs_version\": \"cFE %d.%d\","
            "\"mcp_interface_status\": {"
            "\"app_id\": %u,"
            "\"execution_counter\": %u,"
            "\"active_clients\": %u,"
            "\"total_requests\": %u,"
            "\"successful_requests\": %u,"
            "\"failed_requests\": %u,"
            "\"safety_mode\": %s,"
            "\"debug_mode\": %s"
            "},"
            "\"memory_status\": {"
            "\"available_memory\": \"unknown\","
            "\"used_memory\": \"unknown\""
            "},"
            "\"task_status\": {"
            "\"total_tasks\": \"unknown\","
            "\"active_tasks\": \"unknown\""
            "}"
            "}"
            "}",
            current_time,
            CFE_MAJOR_VERSION, CFE_MINOR_VERSION,
            (status == CFE_SUCCESS) ? app_info.AppId : 0,
            (status == CFE_SUCCESS) ? app_info.ExecutionCounter : 0,
            MCP_INTERFACE_AppData.ActiveClients,
            MCP_INTERFACE_AppData.RequestCounter,
            MCP_INTERFACE_AppData.SuccessCounter,
            MCP_INTERFACE_AppData.ErrorCounter,
            MCP_INTERFACE_AppData.SafetyMode ? "true" : "false",
            MCP_INTERFACE_AppData.DebugMode ? "true" : "false");

    response->status = 0;
    strncpy(response->result, result_str, sizeof(response->result) - 1);

    return CFE_SUCCESS;

} /* End MCP_INTERFACE_HandleGetSystemStatus */

/*
** Handle Manage App request
*/
int32 MCP_INTERFACE_HandleManageApp(MCP_Request_t *request, MCP_Response_t *response)
{
    int32 status;
    char result_str[512];
    CFE_ES_AppInfo_t app_info;

    /* Validate app name */
    if (strlen(request->app_name) == 0)
    {
        response->status = -1;
        strncpy(response->error_msg, "App name is required", sizeof(response->error_msg) - 1);
        return CFE_ES_ERR_APPNAME;
    }

    /* Parse action from params */
    if (strcmp(request->params, "\"start\"") == 0)
    {
        /* Start application - this is a critical operation */
        if (!MCP_INTERFACE_AppData.SafetyMode || request->require_confirmation)
        {
            /* In a real implementation, this would start the app */
            snprintf(result_str, sizeof(result_str),
                    "{\"action\": \"start\", \"app\": \"%s\", \"status\": \"not_implemented\"}",
                    request->app_name);
            
            CFE_EVS_SendEvent(MCP_INTERFACE_COMMAND_SUCCESS_INF_EID,
                             CFE_EVS_INFORMATION,
                             "MCP_INTERFACE: App start requested for %s", request->app_name);
        }
        else
        {
            response->status = -1;
            strncpy(response->error_msg, "App start requires confirmation in safety mode", sizeof(response->error_msg) - 1);
            return CFE_ES_ERR_APPNAME;
        }
    }
    else if (strcmp(request->params, "\"stop\"") == 0)
    {
        /* Stop application - this is a critical operation */
        if (!MCP_INTERFACE_AppData.SafetyMode || request->require_confirmation)
        {
            /* In a real implementation, this would stop the app */
            snprintf(result_str, sizeof(result_str),
                    "{\"action\": \"stop\", \"app\": \"%s\", \"status\": \"not_implemented\"}",
                    request->app_name);
            
            CFE_EVS_SendEvent(MCP_INTERFACE_COMMAND_SUCCESS_INF_EID,
                             CFE_EVS_INFORMATION,
                             "MCP_INTERFACE: App stop requested for %s", request->app_name);
        }
        else
        {
            response->status = -1;
            strncpy(response->error_msg, "App stop requires confirmation in safety mode", sizeof(response->error_msg) - 1);
            return CFE_ES_ERR_APPNAME;
        }
    }
    else if (strcmp(request->params, "\"status\"") == 0)
    {
        /* Get app status */
        status = CFE_ES_GetAppInfo(&app_info, request->app_name);
        if (status == CFE_SUCCESS)
        {
            snprintf(result_str, sizeof(result_str),
                    "{"
                    "\"action\": \"status\","
                    "\"app\": \"%s\","
                    "\"app_id\": %u,"
                    "\"execution_counter\": %u,"
                    "\"app_state\": %u,"
                    "\"stack_size\": %u,"
                    "\"address_space_id\": %u"
                    "}",
                    request->app_name,
                    app_info.AppId,
                    app_info.ExecutionCounter,
                    app_info.AppState,
                    app_info.StackSize,
                    app_info.AddressSpaceId);
        }
        else
        {
            snprintf(result_str, sizeof(result_str),
                    "{\"action\": \"status\", \"app\": \"%s\", \"error\": \"App not found or error getting info\"}",
                    request->app_name);
        }
    }
    else
    {
        response->status = -1;
        snprintf(response->error_msg, sizeof(response->error_msg),
                "Unknown action in params: %s", request->params);
        return CFE_ES_ERR_APPNAME;
    }

    response->status = 0;
    strncpy(response->result, result_str, sizeof(response->result) - 1);

    return CFE_SUCCESS;

} /* End MCP_INTERFACE_HandleManageApp */

/*
** Handle Get File List request
*/
int32 MCP_INTERFACE_HandleGetFileList(MCP_Request_t *request, MCP_Response_t *response)
{
    DIR *dir;
    struct dirent *entry;
    struct stat file_stat;
    char result_str[2048];
    char file_path[256];
    char *directory = "/cf"; /* Default cFS file system directory */
    int file_count = 0;
    
    /* Parse directory from params if provided */
    if (strlen(request->params) > 2)
    {
        /* Remove quotes from JSON string */
        strncpy(file_path, request->params + 1, sizeof(file_path) - 1);
        file_path[strlen(file_path) - 1] = '\0';
        directory = file_path;
    }

    /* Open directory */
    dir = opendir(directory);
    if (dir == NULL)
    {
        response->status = -1;
        snprintf(response->error_msg, sizeof(response->error_msg),
                "Failed to open directory: %s", directory);
        return CFE_ES_ERR_APPNAME;
    }

    /* Start building JSON response */
    snprintf(result_str, sizeof(result_str),
            "{\"directory\": \"%s\", \"files\": [", directory);

    /* Read directory entries */
    while ((entry = readdir(dir)) != NULL && file_count < 50)
    {
        /* Skip . and .. */
        if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0)
            continue;

        /* Get file stats */
        snprintf(file_path, sizeof(file_path), "%s/%s", directory, entry->d_name);
        if (stat(file_path, &file_stat) == 0)
        {
            if (file_count > 0)
            {
                strncat(result_str, ", ", sizeof(result_str) - strlen(result_str) - 1);
            }
            
            /* Add file info to JSON */
            char file_info[256];
            snprintf(file_info, sizeof(file_info),
                    "{\"name\": \"%s\", \"size\": %ld, \"type\": \"%s\"}",
                    entry->d_name,
                    file_stat.st_size,
                    S_ISDIR(file_stat.st_mode) ? "directory" : "file");
            
            strncat(result_str, file_info, sizeof(result_str) - strlen(result_str) - 1);
            file_count++;
        }
    }

    strncat(result_str, "]}", sizeof(result_str) - strlen(result_str) - 1);
    closedir(dir);

    response->status = 0;
    strncpy(response->result, result_str, sizeof(response->result) - 1);

    return CFE_SUCCESS;

} /* End MCP_INTERFACE_HandleGetFileList */

/*
** Handle Read File request
*/
int32 MCP_INTERFACE_HandleReadFile(MCP_Request_t *request, MCP_Response_t *response)
{
    FILE *file;
    char file_path[256];
    char file_content[1024];
    char result_str[2048];
    size_t bytes_read;

    /* Parse file path from params */
    if (strlen(request->params) < 3)
    {
        response->status = -1;
        strncpy(response->error_msg, "File path is required", sizeof(response->error_msg) - 1);
        return CFE_ES_ERR_APPNAME;
    }

    /* Remove quotes from JSON string */
    strncpy(file_path, request->params + 1, sizeof(file_path) - 1);
    file_path[strlen(file_path) - 1] = '\0';

    /* Safety check - only allow reading from certain directories */
    if (strstr(file_path, "..") != NULL || file_path[0] != '/')
    {
        response->status = -1;
        strncpy(response->error_msg, "Invalid file path", sizeof(response->error_msg) - 1);
        return CFE_ES_ERR_APPNAME;
    }

    /* Open file */
    file = fopen(file_path, "r");
    if (file == NULL)
    {
        response->status = -1;
        snprintf(response->error_msg, sizeof(response->error_msg),
                "Failed to open file: %s", file_path);
        return CFE_ES_ERR_APPNAME;
    }

    /* Read file content (limited to avoid buffer overflow) */
    bytes_read = fread(file_content, 1, sizeof(file_content) - 1, file);
    file_content[bytes_read] = '\0';
    fclose(file);

    /* Create JSON response */
    snprintf(result_str, sizeof(result_str),
            "{\"file_path\": \"%s\", \"size\": %zu, \"content\": \"%s\"}",
            file_path, bytes_read, file_content);

    response->status = 0;
    strncpy(response->result, result_str, sizeof(response->result) - 1);

    return CFE_SUCCESS;

} /* End MCP_INTERFACE_HandleReadFile */

/*
** Handle Write File request
*/
int32 MCP_INTERFACE_HandleWriteFile(MCP_Request_t *request, MCP_Response_t *response)
{
    /* File writing is a critical operation - require confirmation in safety mode */
    if (MCP_INTERFACE_AppData.SafetyMode && !request->require_confirmation)
    {
        response->status = -1;
        strncpy(response->error_msg, "File write requires confirmation in safety mode", sizeof(response->error_msg) - 1);
        return CFE_ES_ERR_APPNAME;
    }

    /* For safety, file writing is not implemented in this demo */
    response->status = -1;
    strncpy(response->error_msg, "File write operation not implemented for safety reasons", sizeof(response->error_msg) - 1);

    CFE_EVS_SendEvent(MCP_INTERFACE_SAFETY_ERR_EID,
                     CFE_EVS_ERROR,
                     "MCP_INTERFACE: File write operation blocked for safety");

    return CFE_ES_ERR_APPNAME;

} /* End MCP_INTERFACE_HandleWriteFile */

/*
** Handle Get Event Log request
*/
int32 MCP_INTERFACE_HandleGetEventLog(MCP_Request_t *request, MCP_Response_t *response)
{
    char result_str[2048];

    /* This is a simplified implementation - real version would access EVS log */
    snprintf(result_str, sizeof(result_str),
            "{"
            "\"event_log\": {"
            "\"timestamp\": %u,"
            "\"message\": \"Event log access not fully implemented\","
            "\"recent_events\": ["
            "{"
            "\"id\": 1,"
            "\"app\": \"MCP_INTERFACE\","
            "\"type\": \"INFO\","
            "\"message\": \"MCP Interface App Started\""
            "},"
            "{"
            "\"id\": 2,"
            "\"app\": \"MCP_INTERFACE\","
            "\"type\": \"INFO\","
            "\"message\": \"Client connected\""
            "}"
            "]"
            "}"
            "}",
            CFE_TIME_GetTime().Seconds);

    response->status = 0;
    strncpy(response->result, result_str, sizeof(response->result) - 1);

    return CFE_SUCCESS;

} /* End MCP_INTERFACE_HandleGetEventLog */

/*
** Handle Emergency Stop request
*/
int32 MCP_INTERFACE_HandleEmergencyStop(MCP_Request_t *request, MCP_Response_t *response)
{
    char result_str[512];

    /* Log emergency stop event */
    CFE_EVS_SendEvent(MCP_INTERFACE_SAFETY_ERR_EID,
                     CFE_EVS_CRITICAL,
                     "MCP_INTERFACE: EMERGENCY STOP requested via MCP interface");

    /* In a real implementation, this would:
     * 1. Stop all non-essential applications
     * 2. Put system in safe mode
     * 3. Alert ground control
     * 4. Log the event
     */

    /* Enable safety mode */
    MCP_INTERFACE_AppData.SafetyMode = TRUE;

    snprintf(result_str, sizeof(result_str),
            "{"
            "\"emergency_stop\": {"
            "\"timestamp\": %u,"
            "\"status\": \"executed\","
            "\"actions\": [\"safety_mode_enabled\", \"event_logged\"],"
            "\"message\": \"Emergency stop procedure initiated\""
            "}"
            "}",
            CFE_TIME_GetTime().Seconds);

    response->status = 0;
    strncpy(response->result, result_str, sizeof(response->result) - 1);

    return CFE_SUCCESS;

} /* End MCP_INTERFACE_HandleEmergencyStop */
