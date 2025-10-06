/*
** MCP Interface Safety and Utility Functions
**
** This file contains safety checks, validation functions, and utilities
** for the cFS MCP Interface Application.
*/

/*
** Include Files
*/
#include "mcp_interface_app.h"
#include <cjson/cJSON.h>

/*
** List of commands that require confirmation
*/
static const char* critical_commands[] = {
    "RESET",
    "RESTART",
    "STOP",
    "START",
    "DELETE",
    "FORMAT",
    "POWER_OFF",
    "REBOOT",
    NULL
};

/*
** List of apps that are critical to system operation
*/
static const char* critical_apps[] = {
    "CFE_ES",
    "CFE_EVS",
    "CFE_SB",
    "CFE_TIME",
    "CFE_TBL",
    "SCH_LAB",
    NULL
};

/*
** Safety check for commands
*/
boolean MCP_INTERFACE_IsSafeCommand(MCP_Request_t *request)
{
    int i;
    char upper_command[MCP_MAX_CMD_NAME_LEN];
    char upper_app[MCP_MAX_APP_NAME_LEN];

    /* Convert command to uppercase for comparison */
    for (i = 0; i < strlen(request->command) && i < sizeof(upper_command) - 1; i++)
    {
        upper_command[i] = toupper(request->command[i]);
    }
    upper_command[i] = '\0';

    /* Convert app name to uppercase for comparison */
    for (i = 0; i < strlen(request->app_name) && i < sizeof(upper_app) - 1; i++)
    {
        upper_app[i] = toupper(request->app_name[i]);
    }
    upper_app[i] = '\0';

    /* Check if command is in critical command list */
    for (i = 0; critical_commands[i] != NULL; i++)
    {
        if (strstr(upper_command, critical_commands[i]) != NULL)
        {
            /* Critical command found */
            if (MCP_INTERFACE_AppData.SafetyMode && !request->require_confirmation)
            {
                CFE_EVS_SendEvent(MCP_INTERFACE_SAFETY_ERR_EID,
                                CFE_EVS_ERROR,
                                "MCP_INTERFACE: Critical command '%s' blocked - requires confirmation",
                                request->command);
                return FALSE;
            }
        }
    }

    /* Check if app is critical */
    for (i = 0; critical_apps[i] != NULL; i++)
    {
        if (strcmp(upper_app, critical_apps[i]) == 0)
        {
            /* Operating on critical app */
            if (MCP_INTERFACE_AppData.SafetyMode && !request->require_confirmation)
            {
                CFE_EVS_SendEvent(MCP_INTERFACE_SAFETY_ERR_EID,
                                CFE_EVS_ERROR,
                                "MCP_INTERFACE: Command to critical app '%s' blocked - requires confirmation",
                                request->app_name);
                return FALSE;
            }
        }
    }

    /* Check for file operations that could be dangerous */
    if (request->type == MCP_CMD_WRITE_FILE || request->type == MCP_CMD_READ_FILE)
    {
        /* Check if trying to access system files */
        if (strstr(request->params, "/boot") != NULL ||
            strstr(request->params, "/etc") != NULL ||
            strstr(request->params, "/sys") != NULL ||
            strstr(request->params, "/proc") != NULL)
        {
            CFE_EVS_SendEvent(MCP_INTERFACE_SAFETY_ERR_EID,
                            CFE_EVS_ERROR,
                            "MCP_INTERFACE: File operation blocked - system directory access denied");
            return FALSE;
        }
    }

    /* Emergency stop is always allowed */
    if (request->type == MCP_CMD_EMERGENCY_STOP)
    {
        return TRUE;
    }

    return TRUE;

} /* End MCP_INTERFACE_IsSafeCommand */

/*
** Check if command requires confirmation
*/
boolean MCP_INTERFACE_RequiresConfirmation(MCP_Request_t *request)
{
    int i;
    char upper_command[MCP_MAX_CMD_NAME_LEN];

    /* Convert command to uppercase for comparison */
    for (i = 0; i < strlen(request->command) && i < sizeof(upper_command) - 1; i++)
    {
        upper_command[i] = toupper(request->command[i]);
    }
    upper_command[i] = '\0';

    /* Check if command is in critical command list */
    for (i = 0; critical_commands[i] != NULL; i++)
    {
        if (strstr(upper_command, critical_commands[i]) != NULL)
        {
            return TRUE;
        }
    }

    /* File write operations require confirmation */
    if (request->type == MCP_CMD_WRITE_FILE)
    {
        return TRUE;
    }

    /* App management operations require confirmation */
    if (request->type == MCP_CMD_MANAGE_APP)
    {
        if (strstr(request->params, "start") != NULL ||
            strstr(request->params, "stop") != NULL ||
            strstr(request->params, "restart") != NULL)
        {
            return TRUE;
        }
    }

    return FALSE;

} /* End MCP_INTERFACE_RequiresConfirmation */

/*
** Validate MCP request
*/
int32 MCP_INTERFACE_ValidateRequest(MCP_Request_t *request)
{
    /* Check request ID */
    if (request->id == 0)
    {
        return CFE_ES_ERR_APPNAME;
    }

    /* Check command type */
    if (request->type >= MCP_CMD_MAX)
    {
        return CFE_ES_ERR_APPNAME;
    }

    /* Validate app name for commands that require it */
    if (request->type == MCP_CMD_SEND_COMMAND ||
        request->type == MCP_CMD_GET_TELEMETRY ||
        request->type == MCP_CMD_MANAGE_APP)
    {
        if (strlen(request->app_name) == 0 || strlen(request->app_name) >= MCP_MAX_APP_NAME_LEN)
        {
            return CFE_ES_ERR_APPNAME;
        }
    }

    /* Validate command name for send command */
    if (request->type == MCP_CMD_SEND_COMMAND)
    {
        if (strlen(request->command) == 0 || strlen(request->command) >= MCP_MAX_CMD_NAME_LEN)
        {
            return CFE_ES_ERR_APPNAME;
        }
    }

    /* Check parameters length */
    if (strlen(request->params) >= MCP_MAX_JSON_SIZE)
    {
        return CFE_ES_ERR_APPNAME;
    }

    return CFE_SUCCESS;

} /* End MCP_INTERFACE_ValidateRequest */

/*
** Log safety event
*/
void MCP_INTERFACE_LogSafetyEvent(const char *event_msg, uint32 event_id)
{
    CFE_EVS_SendEvent(event_id,
                     CFE_EVS_ERROR,
                     "MCP_INTERFACE SAFETY: %s", event_msg);

    /* In a real implementation, this would also:
     * 1. Log to persistent storage
     * 2. Send alert to ground control
     * 3. Update system status
     */

} /* End MCP_INTERFACE_LogSafetyEvent */

/*
** Parse JSON request
*/
int32 MCP_INTERFACE_ParseJSONRequest(const char *json_str, MCP_Request_t *request)
{
    cJSON *json = NULL;
    cJSON *id = NULL;
    cJSON *type = NULL;
    cJSON *app_name = NULL;
    cJSON *command = NULL;
    cJSON *params = NULL;
    cJSON *require_confirmation = NULL;
    cJSON *is_critical = NULL;
    int32 status = CFE_SUCCESS;

    /* Initialize request structure */
    memset(request, 0, sizeof(MCP_Request_t));

    /* Parse JSON */
    json = cJSON_Parse(json_str);
    if (json == NULL)
    {
        return CFE_ES_ERR_APPNAME;
    }

    /* Extract fields */
    id = cJSON_GetObjectItem(json, "id");
    if (cJSON_IsNumber(id))
    {
        request->id = (uint32)id->valueint;
    }
    else
    {
        status = CFE_ES_ERR_APPNAME;
        goto cleanup;
    }

    type = cJSON_GetObjectItem(json, "type");
    if (cJSON_IsNumber(type))
    {
        request->type = (MCP_CommandType_t)type->valueint;
    }
    else
    {
        status = CFE_ES_ERR_APPNAME;
        goto cleanup;
    }

    app_name = cJSON_GetObjectItem(json, "app_name");
    if (cJSON_IsString(app_name) && app_name->valuestring != NULL)
    {
        strncpy(request->app_name, app_name->valuestring, sizeof(request->app_name) - 1);
    }

    command = cJSON_GetObjectItem(json, "command");
    if (cJSON_IsString(command) && command->valuestring != NULL)
    {
        strncpy(request->command, command->valuestring, sizeof(request->command) - 1);
    }

    params = cJSON_GetObjectItem(json, "params");
    if (cJSON_IsString(params) && params->valuestring != NULL)
    {
        strncpy(request->params, params->valuestring, sizeof(request->params) - 1);
    }

    require_confirmation = cJSON_GetObjectItem(json, "require_confirmation");
    if (cJSON_IsBool(require_confirmation))
    {
        request->require_confirmation = cJSON_IsTrue(require_confirmation);
    }

    is_critical = cJSON_GetObjectItem(json, "is_critical");
    if (cJSON_IsBool(is_critical))
    {
        request->is_critical = cJSON_IsTrue(is_critical);
    }

cleanup:
    cJSON_Delete(json);
    return status;

} /* End MCP_INTERFACE_ParseJSONRequest */

/*
** Format JSON response
*/
int32 MCP_INTERFACE_FormatJSONResponse(MCP_Response_t *response, char *json_str, uint32 max_len)
{
    cJSON *json = NULL;
    char *json_string = NULL;
    int32 status = CFE_SUCCESS;

    /* Create JSON object */
    json = cJSON_CreateObject();
    if (json == NULL)
    {
        return CFE_ES_ERR_APPNAME;
    }

    /* Add fields */
    cJSON_AddNumberToObject(json, "id", response->id);
    cJSON_AddNumberToObject(json, "status", response->status);
    cJSON_AddNumberToObject(json, "timestamp", response->timestamp);

    if (response->status == 0)
    {
        /* Success - add result */
        cJSON *result_json = cJSON_Parse(response->result);
        if (result_json != NULL)
        {
            cJSON_AddItemToObject(json, "result", result_json);
        }
        else
        {
            cJSON_AddStringToObject(json, "result", response->result);
        }
    }
    else
    {
        /* Error - add error message */
        cJSON_AddStringToObject(json, "error", response->error_msg);
    }

    /* Convert to string */
    json_string = cJSON_Print(json);
    if (json_string == NULL)
    {
        status = CFE_ES_ERR_APPNAME;
        goto cleanup;
    }

    /* Copy to output buffer */
    if (strlen(json_string) >= max_len)
    {
        status = CFE_ES_ERR_APPNAME;
        goto cleanup;
    }

    strcpy(json_str, json_string);

cleanup:
    if (json_string != NULL)
    {
        free(json_string);
    }
    cJSON_Delete(json);
    return status;

} /* End MCP_INTERFACE_FormatJSONResponse */

/*
** Send MCP response
*/
int32 MCP_INTERFACE_SendMCPResponse(int32 client_socket, MCP_Response_t *response)
{
    char json_str[MCP_MAX_JSON_SIZE];
    ssize_t bytes_sent;
    int32 status;

    /* Format response as JSON */
    status = MCP_INTERFACE_FormatJSONResponse(response, json_str, sizeof(json_str));
    if (status != CFE_SUCCESS)
    {
        /* Send simple error response */
        snprintf(json_str, sizeof(json_str),
                "{\"id\": %u, \"status\": -1, \"error\": \"Failed to format response\", \"timestamp\": %u}",
                response->id, response->timestamp);
    }

    /* Send response */
    bytes_sent = send(client_socket, json_str, strlen(json_str), MSG_NOSIGNAL);
    if (bytes_sent < 0)
    {
        CFE_EVS_SendEvent(MCP_INTERFACE_COMMAND_ERR_EID,
                         CFE_EVS_ERROR,
                         "MCP_INTERFACE: Failed to send response to client");
        return CFE_ES_ERR_APPNAME;
    }

    if (MCP_INTERFACE_AppData.DebugMode)
    {
        CFE_EVS_SendEvent(MCP_INTERFACE_COMMAND_SUCCESS_INF_EID,
                         CFE_EVS_INFORMATION,
                         "MCP_INTERFACE: Response sent: %s", json_str);
    }

    return CFE_SUCCESS;

} /* End MCP_INTERFACE_SendMCPResponse */
