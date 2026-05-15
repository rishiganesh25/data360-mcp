import json
import logging
import time
import difflib
import threading
from collections import defaultdict
from typing import Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from mcp.server.fastmcp import FastMCP
from pydantic import Field
import requests
import os
from oauth import OAuthConfig, OAuthSession
from connect_api_dc_sql import run_query
from connect_api_datacloud import (
    get_data_streams,
    get_data_stream_details,
    get_data_model_objects,
    get_data_model_object_details,
    get_data_stream_mappings,
    get_identity_resolution_rulesets,
    get_calculated_insights,
    create_calculated_insight as _create_calculated_insight,
    get_segments,
    create_segment as _create_segment,
    create_segment_dbt as _create_segment_dbt,
    describe_sobject as _describe_sobject,
    create_sobject_record as _create_sobject_record,
    get_data_graphs,
    create_data_graph as _create_data_graph,
    delete_data_graph as _delete_data_graph,
    refresh_data_stream,
    create_data_stream,
    create_ingestion_api_schema,
    delete_data_stream,
    list_connectors as _list_connectors,
    get_connector_source_objects as _get_connector_source_objects,
    list_connector_source_objects,
    get_retrievers,
    get_search_indexes,
    create_dlo_dmo_mapping as _create_dlo_dmo_mapping,
    create_custom_dmo_field as _create_custom_dmo_field,
    delete_custom_dmo_fields as _delete_custom_dmo_fields,
    delete_dlo_dmo_mapping as _delete_dlo_dmo_mapping,
    update_dlo_dmo_mapping as _update_dlo_dmo_mapping,
    create_custom_dmo as _create_custom_dmo,
    get_activations as _get_activations,
    get_activation_by_id as _get_activation_by_id,
    delete_activation as _delete_activation,
    update_activation as _update_activation,
    get_ssot_connectors as _get_ssot_connectors,
    get_ssot_connector_metadata as _get_ssot_connector_metadata,
    get_data_action_targets as _get_data_action_targets,
    get_data_action_target_by_name as _get_data_action_target_by_name,
    create_data_action_target as _create_data_action_target,
    delete_data_action_target as _delete_data_action_target,
    get_data_actions as _get_data_actions,
    create_data_action as _create_data_action,
    get_data_graph_metadata as _get_data_graph_metadata,
    create_data_lake_object as _create_data_lake_object,
    update_data_lake_object as _update_data_lake_object,
    delete_data_lake_object as _delete_data_lake_object,
    get_data_spaces as _get_data_spaces,
    get_data_space_by_id as _get_data_space_by_id,
    update_data_space as _update_data_space,
    get_data_space_members as _get_data_space_members,
    get_data_space_member as _get_data_space_member,
    create_data_transform as _create_data_transform,
    update_data_transform as _update_data_transform,
    delete_data_transform as _delete_data_transform,
    get_data_transform_run_history as _get_data_transform_run_history,
    update_segment as _update_segment,
    delete_segment as _delete_segment,
)

# Get logger for this module
logger = logging.getLogger(__name__)


# Create an MCP server
mcp = FastMCP("Demo")

# Global config and session
sf_org: OAuthConfig = OAuthConfig.from_env()
oauth_session: OAuthSession = OAuthSession(sf_org)

# Non-auth configuration
DEFAULT_LIST_TABLE_FILTER = os.getenv('DEFAULT_LIST_TABLE_FILTER', '%')


@mcp.tool(description="Executes a SQL query and returns the results")
def query(
    sql: str = Field(
        description="A SQL query in the PostgreSQL dialect make sure to always quote all identifies and use the exact casing. To formulate the query first verify which tables and fields to use through the suggest fields tool (or if it is broken through the list tables / describe tables call). Before executing the tool provide the user a succinct summary (targeted to low code users) on the semantics of the query"),
):
    # Returns both data and metadata
    return run_query(oauth_session, sql)


@mcp.tool(description="Lists the available tables in the database")
def list_tables() -> list[str]:
    sql = "SELECT c.relname AS TABLE_NAME FROM pg_catalog.pg_namespace n, pg_catalog.pg_class c LEFT JOIN pg_catalog.pg_description d ON (c.oid = d.objoid AND d.objsubid = 0  and d.classoid = 'pg_class'::regclass) WHERE c.relnamespace = n.oid AND c.relname LIKE '%s'" % DEFAULT_LIST_TABLE_FILTER
    result = run_query(oauth_session, sql)
    # Extract data from the result dictionary
    data = result.get("data", [])
    return [x[0] for x in data]


@mcp.tool(description="Describes the columns of a table")
def describe_table(
    table: str = Field(description="The table name"),
) -> list[str]:
    import re
    if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', table):
        return [f"error: invalid table name '{table}'"]
    safe_table = table.replace("'", "''")
    sql = "SELECT a.attname FROM pg_catalog.pg_namespace n JOIN pg_catalog.pg_class c ON (c.relnamespace = n.oid) JOIN pg_catalog.pg_attribute a ON (a.attrelid = c.oid) JOIN pg_catalog.pg_type t ON (a.atttypid = t.oid) LEFT JOIN pg_catalog.pg_attrdef def ON (a.attrelid = def.adrelid AND a.attnum = def.adnum) LEFT JOIN pg_catalog.pg_description dsc ON (c.oid = dsc.objoid AND a.attnum = dsc.objsubid) LEFT JOIN pg_catalog.pg_class dc ON (dc.oid = dsc.classoid AND dc.relname = 'pg_class') LEFT JOIN pg_catalog.pg_namespace dn ON (dc.relnamespace = dn.oid AND dn.nspname = 'pg_catalog') WHERE a.attnum > 0 AND NOT a.attisdropped AND c.relname='%s'" % safe_table
    result = run_query(oauth_session, sql)
    data = result.get("data", [])
    return [x[0] for x in data]


# ============================================================================
# DATA CLOUD MANAGEMENT TOOLS
# ============================================================================

@mcp.tool(description="Lists all data streams with their status (Active, Inactive, Processing, etc.)")
def list_data_streams() -> list[dict]:
    """
    Get all data streams with their current status.
    Returns information like name, status, source object, category, and last refresh date.
    """
    try:
        result = get_data_streams(oauth_session)
        # Handle different response formats
        if isinstance(result, dict):
            return result.get("dataStreams", result.get("data", [result]))
        return result
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description="Gets detailed information about a specific data stream including its configuration and mappings")
def get_data_stream_info(
    data_stream_name: str = Field(description="The API name of the data stream (e.g., 'OrdersHistory__dll')"),
) -> dict:
    """
    Get detailed information about a specific data stream.
    """
    try:
        return get_data_stream_details(oauth_session, data_stream_name)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Lists all Data Model Objects (DMOs) in the org")
def list_data_model_objects() -> list[dict]:
    """
    Get all Data Model Objects with their metadata.
    DMOs are the target objects that data streams map to.
    """
    try:
        result = get_data_model_objects(oauth_session)
        if isinstance(result, dict):
            return result.get("dataModelObjects", result.get("data", [result]))
        return result
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description="Gets detailed information about a specific Data Model Object including fields and relationships")
def get_dmo_details(
    dmo_name: str = Field(description="The API name of the DMO (e.g., 'ssot__Individual__dlm')"),
) -> dict:
    """
    Get detailed information about a specific Data Model Object.
    """
    try:
        return get_data_model_object_details(oauth_session, dmo_name)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Lists all data stream to DMO mappings showing how source data maps to the data model")
def list_mappings() -> list[dict]:
    """
    Get all data stream to Data Model Object mappings.
    Shows the field-level mappings between source and target.
    """
    try:
        result = get_data_stream_mappings(oauth_session)
        if isinstance(result, dict):
            return result.get("mappings", result.get("data", [result]))
        return result
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description="Lists all identity resolution rulesets used for matching and reconciling customer profiles")
def list_identity_rulesets() -> list[dict]:
    """
    Get all identity resolution rulesets.
    These define how profiles are matched and unified.
    """
    try:
        result = get_identity_resolution_rulesets(oauth_session)
        if isinstance(result, dict):
            return result.get("rulesets", result.get("data", [result]))
        return result
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description="Lists all calculated insights defined in Data Cloud")
def list_calculated_insights() -> list[dict]:
    """
    Get all calculated insights.
    Calculated insights are derived metrics computed from your data.
    """
    try:
        result = get_calculated_insights(oauth_session)
        if isinstance(result, dict):
            return result.get("calculatedInsights", result.get("data", [result]))
        return result
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description=(
    "Creates a Calculated Insight in Data Cloud from a SQL expression. "
    "CIs are SQL-defined derived metrics (e.g., Customer LTV, engagement score) that "
    "materialize as a DMO and can be used in segments and activations. Dimensions and "
    "measures are inferred from the SQL SELECT list — every projected column must be "
    "aliased and ends up as either a dimension (GROUP BY keys) or a measure (aggregates)."
))
def create_calculated_insight(
    api_name: str = Field(
        description="The API/developer name for the CI. Must end in '__cio' (e.g., 'customer_ltv__cio')."),
    display_name: str = Field(
        description="Human-readable label shown in the Data Cloud UI (e.g., 'Customer Lifetime Value')."),
    expression: str = Field(
        description=(
            "The SELECT SQL expression. Reference DMO fields as <DMO>.<field>. "
            "Every projected column must be aliased (the alias becomes the CI field name). "
            "Example: 'SELECT OrdersData__dlm.Individual_Id__c AS individual_id__c, "
            "SUM(OrdersData__dlm.OrderPrice__c) AS total_spend__c "
            "FROM OrdersData__dlm GROUP BY OrdersData__dlm.Individual_Id__c'"
        )),
    description: str = Field(
        default="",
        description="Optional description of what this CI computes."),
    data_space: str = Field(
        default="default",
        description="The dataspace to deploy into (default: 'default')."),
    publish_schedule_interval: str = Field(
        default="Six",
        description="Refresh interval enum. Known values: 'Six' (6-hour). Default: 6-hour."),
    publish_schedule_start: str = Field(
        default="",
        description="Optional ISO datetime for first run (e.g., '2026-05-05T02:00'). Defaults to a past date so the CI processes immediately."),
) -> dict:
    """
    Create a Calculated Insight (SQL-defined derived metric) in Data Cloud.
    """
    try:
        return _create_calculated_insight(
            oauth_session,
            api_name=api_name,
            display_name=display_name,
            expression=expression,
            description=description,
            data_space=data_space,
            publish_schedule_interval=publish_schedule_interval,
            publish_schedule_start=publish_schedule_start or None,
        )
    except Exception as e:
        return {"error": str(e), "apiName": api_name}


@mcp.tool(description="Lists all segments defined in Data Cloud")
def list_segments() -> list[dict]:
    """
    Get all segments.
    Segments are groups of individuals based on specific criteria.
    """
    try:
        result = get_segments(oauth_session)
        if isinstance(result, dict):
            return result.get("segments", result.get("data", [result]))
        return result
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description=(
    "Updates an existing segment in Data Cloud by its API name. Accepts a JSON payload with "
    "any combination of: developerName, displayName, description, segmentOnApiName, "
    "publishSchedule, publishScheduleEndDate, publishScheduleStartDateTime, "
    "additionalMetadata, includeCriteria or includeDbt (for DBT/SQL segments with models), "
    "segmentType ('Standard' or 'Dbt'). Only include fields you want to change."
))
def update_segment(
    segment_api_name: str = Field(description="The API name of the segment to update"),
    payload: str = Field(
        description=(
            "JSON string with the fields to update. Example for DBT segment: "
            '{"developerName": "...", "description": "...", "segmentType": "Dbt", '
            '"includeDbt": {"models": {"models": [{"name": "m1", "sql": "SELECT ..."}]}}, '
            '"publishSchedule": "One"}'
        )),
) -> dict:
    """
    Update a segment in Data Cloud.
    """
    try:
        parsed = json.loads(payload)
        return _update_segment(oauth_session, segment_api_name, parsed)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in payload: {e}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Deletes a segment by its API name. WARNING: This permanently removes the segment.")
def delete_segment(
    segment_api_name: str = Field(description="The API name of the segment to delete"),
) -> dict:
    """
    Delete a segment from Data Cloud.
    """
    try:
        return _delete_segment(oauth_session, segment_api_name)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Creates a new segment in Data Cloud from a JSON segment definition")
def create_segment(
    segment_definition: str = Field(
        description=(
            "JSON string with the full segment definition. Must include: "
            "apiName, displayName, segmentOnApiName, dataSpace, "
            "includeCriteria (nested filter JSON), lookbackPeriod (e.g. 'P90D'), "
            "and publishInterval (e.g. 'NO_REFRESH' or 'DAILY')."
        )),
) -> dict:
    """
    Create a new segment in Data Cloud.
    The segment definition should follow the Data Cloud segment schema.
    """
    try:
        parsed = json.loads(segment_definition)
        return _create_segment(oauth_session, parsed)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in segment_definition: {e}"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# ACTIVATIONS
# ============================================================================

@mcp.tool(description=(
    "Lists all Data Cloud segment activations. Returns activation target, status, "
    "refresh type, associated segment, publish status, and schedule details. "
    "Supports pagination via batch_size and offset."
))
def list_activations(
    batch_size: int = Field(default=25, description="Number of activations per page"),
    offset: int = Field(default=0, description="Offset for pagination (0-based)"),
    order_by: str = Field(default="createddate desc", description="Order-by expression (e.g. 'createddate desc', 'name asc')"),
) -> list[dict]:
    """
    Get all segment activations from Data Cloud.
    Activations define how segments are published to external targets (S3, Marketing Cloud, etc.).
    """
    try:
        result = _get_activations(oauth_session, batch_size=batch_size, offset=offset, order_by=order_by)
        if isinstance(result, dict):
            return result.get("activations", result.get("data", [result]))
        return result
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description="Gets detailed information about a specific Data Cloud activation by its ID")
def get_activation_details(
    activation_id: str = Field(description="The activation ID (e.g. '85RVF000000CEf72AG')"),
) -> dict:
    """
    Get full details of a specific activation including its target, segment, status, and schedule.
    """
    try:
        return _get_activation_by_id(oauth_session, activation_id)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description=(
    "Updates a Data Cloud activation by ID. Accepts a JSON payload with any "
    "combination of: refreshType ('INCREMENTAL' or 'FULL'), "
    "relatedDmoFiltersConfig (filters with entityName, filterLimit, and queryPathConfig), "
    "shouldExcludeDeletes (bool), shouldExcludeUpdates (bool), "
    "staticDataConfig (array of name/value pairs). Only include fields you want to change."
))
def update_activation(
    activation_id: str = Field(description="The activation ID to update (e.g. '85RVF000000CEf72AG')"),
    payload: str = Field(
        description=(
            "JSON string with the fields to update. Example: "
            '{"refreshType": "INCREMENTAL", "shouldExcludeDeletes": true, '
            '"shouldExcludeUpdates": true, '
            '"staticDataConfig": {"staticData": [{"name": "key", "value": "val"}]}}'
        )),
) -> dict:
    """
    Update a segment activation in Data Cloud.
    """
    try:
        parsed = json.loads(payload)
        return _update_activation(oauth_session, activation_id, parsed)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in payload: {e}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description=(
    "Lists all SSOT connectors from Data Cloud (activation targets, marketing connectors, etc.) "
    "via the /ssot/connectors endpoint. This is different from list_available_connectors which "
    "returns data source connectors (/ssot/data-connectors)."
))
def list_connectors() -> list[dict]:
    """
    Get all SSOT connectors (activation targets, marketing connectors, etc.).
    """
    try:
        result = _get_ssot_connectors(oauth_session)
        if isinstance(result, dict):
            return result.get("connectors", result.get("data", [result]))
        return result
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description=(
    "Gets metadata for a specific SSOT connector type. Use list_connectors first to "
    "discover available connector types, then pass the type here to get its full metadata."
))
def get_connector_metadata(
    connector_type: str = Field(description="The connector type (e.g. 'SalesforceMarketingCloud', 'AmazonS3', 'GoogleCloudStorage')"),
) -> dict:
    """
    Get metadata for a specific SSOT connector type.
    """
    try:
        return _get_ssot_connector_metadata(oauth_session, connector_type)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Lists all data action targets configured in Data Cloud (e.g. S3, Marketing Cloud, webhook targets).")
def list_data_action_targets() -> list[dict]:
    """
    Get all data action targets.
    """
    try:
        result = _get_data_action_targets(oauth_session)
        if isinstance(result, dict):
            return result.get("dataActionTargets", result.get("data", [result]))
        return result
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description="Gets detailed information about a specific data action target by its API name.")
def get_data_action_target(
    api_name: str = Field(description="The API name of the data action target"),
) -> dict:
    """
    Get details of a specific data action target.
    """
    try:
        return _get_data_action_target_by_name(oauth_session, api_name)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description=(
    "Creates a data action target in Data Cloud. Supports three target types:\n"
    "1. Core — connects to another Salesforce org. Config needs: orgLabel, orgId.\n"
    "2. MarketingCloud — connects to Marketing Cloud. Config needs: "
    "dataActionDestinationType, contentKey, contentTemplate, targetEndpoint.\n"
    "3. WebHook — sends data to a webhook URL. Config needs: targetEndpoint.\n"
    "All types require: type, label, apiName, and a config object."
))
def create_data_action_target(
    target_type: str = Field(description="Target type: 'Core', 'MarketingCloud', or 'WebHook'"),
    label: str = Field(description="Display label for the target (e.g. 'My S3 Target')"),
    api_name: str = Field(description="API name for the target (e.g. 'my_s3_target')"),
    config: str = Field(
        description=(
            "JSON string with the target-specific configuration. Examples:\n"
            'Core: {"orgLabel": "MyCompany Org", "orgId": "00DX2000001ZUi5"}\n'
            'MarketingCloud: {"dataActionDestinationType": "API_EVENT", '
            '"contentKey": "APIEvent-...", "contentTemplate": "API Event Name", '
            '"targetEndpoint": "https://..."}\n'
            'WebHook: {"targetEndpoint": "https://webhook.site/..."}'
        )),
) -> dict:
    """
    Create a data action target (Core, MarketingCloud, or WebHook).
    """
    try:
        parsed_config = json.loads(config)
        payload = {
            "type": target_type,
            "label": label,
            "apiName": api_name,
            "config": parsed_config,
        }
        return _create_data_action_target(oauth_session, payload)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in config: {e}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Deletes a data action target by its API name. WARNING: This permanently removes the target.")
def delete_data_action_target(
    api_name: str = Field(description="The API name of the data action target to delete"),
) -> dict:
    """
    Delete a data action target from Data Cloud.
    """
    try:
        return _delete_data_action_target(oauth_session, api_name)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Lists all data actions configured in Data Cloud.")
def list_data_actions() -> list[dict]:
    """
    Get all data actions from Data Cloud.
    """
    try:
        result = _get_data_actions(oauth_session)
        if isinstance(result, dict):
            return result.get("dataActions", result.get("data", [result]))
        return result
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description=(
    "Creates a data action in Data Cloud. A data action triggers when DMO records change "
    "(create/update/delete) and sends data to one or more data action targets.\n"
    "Required fields: dataActionName, developerName, masterLabel, dataspace, "
    "dataActionTargetNames (array of target API names), dataActionSources (array with "
    "sourceName, sourceType, and sourceCdcSubscriptions like CREATE/UPDATE/DELETE).\n"
    "Optional fields: description, actionConditionExpression, actionConditions, "
    "dataActionEnrichmentProperties, dataActionProjectedFields."
))
def create_data_action(
    data_action_name: str = Field(description="API name for the data action (e.g. 'new_action_from_api')"),
    developer_name: str = Field(description="Developer name (e.g. 'new_action_from_api')"),
    master_label: str = Field(description="Display label (e.g. 'My Data Action')"),
    target_names: str = Field(
        description="JSON array of data action target API names (e.g. '[\"webhook_from_api\"]')"),
    sources: str = Field(
        description=(
            "JSON array of source definitions. Each needs: sourceName (DMO name), "
            "sourceType ('DataModelEntity'), sourceCdcSubscriptions (array of 'CREATE', 'UPDATE', 'DELETE'). "
            'Example: [{"sourceName": "ssot__Account__dlm", "sourceType": "DataModelEntity", '
            '"sourceCdcSubscriptions": ["CREATE", "UPDATE", "DELETE"]}]'
        )),
    dataspace: str = Field(default="default", description="Dataspace name (default: 'default')"),
    description: str = Field(default="", description="Optional description"),
    condition_expression: str = Field(default="", description="Optional action condition expression"),
    conditions: str = Field(default="[]", description="Optional JSON array of action conditions"),
    enrichment_properties: str = Field(default="[]", description="Optional JSON array of enrichment properties"),
    projected_fields: str = Field(default="[]", description="Optional JSON array of projected fields"),
) -> dict:
    """
    Create a data action that triggers on DMO record changes and sends data to targets.
    """
    try:
        parsed_targets = json.loads(target_names)
        parsed_sources = json.loads(sources)
        parsed_conditions = json.loads(conditions)
        parsed_enrichment = json.loads(enrichment_properties)
        parsed_projected = json.loads(projected_fields)

        payload = {
            "dataActionName": data_action_name,
            "developerName": developer_name,
            "masterLabel": master_label,
            "dataActionTargetNames": parsed_targets,
            "dataActionSources": parsed_sources,
            "dataspace": dataspace,
            "description": description,
            "actionConditionExpression": condition_expression,
            "actionConditions": parsed_conditions,
            "dataActionEnrichmentProperties": parsed_enrichment,
            "dataActionProjectedFields": parsed_projected,
        }
        return _create_data_action(oauth_session, payload)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in one of the parameters: {e}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Deletes a Data Cloud activation by its ID. WARNING: This permanently removes the activation.")
def delete_activation(
    activation_id: str = Field(description="The activation ID to delete (e.g. '85RVF000000CEf72AG')"),
) -> dict:
    """
    Delete a segment activation from Data Cloud.
    """
    try:
        return _delete_activation(oauth_session, activation_id)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Creates a DBT (SQL-based) segment in Data Cloud. Automatically discovers the correct API field names.")
def create_segment_dbt(
    display_name: str = Field(description="The display name for the segment"),
    sql: str = Field(description="SQL query selecting the primary key of the segmentOn DMO"),
    description: str = Field(default="", description="Optional description"),
    lookback_period: str = Field(default="P90D", description="Lookback period (e.g., P90D)"),
) -> dict:
    try:
        return _create_segment_dbt(oauth_session, display_name, sql, description, lookback_period)
    except Exception as e:
        return {"error": str(e)}


_SF_REST_ALLOWED_PATH_PREFIXES = [
    "/services/data/",
    "/services/connect/",
]

_SF_REST_BLOCKED_PATH_PATTERNS = [
    "/services/data/v",  # will be combined with suffix checks below
]

_SF_REST_BLOCKED_SUFFIXES = [
    "/composite",
    "/async-queries",
    "/actions/custom",
]


def _is_path_allowed(path: str) -> bool:
    if not any(path.startswith(prefix) for prefix in _SF_REST_ALLOWED_PATH_PREFIXES):
        return False
    path_lower = path.lower()
    for suffix in _SF_REST_BLOCKED_SUFFIXES:
        if suffix in path_lower:
            return False
    return True


@mcp.tool(description=(
    "Makes a Salesforce REST API call scoped to /services/data/ and /services/connect/ paths. "
    "Tooling API is allowed (e.g., /services/data/v63.0/tooling/sobjects/CustomField, "
    "/services/data/v63.0/tooling/query/) so callers can reach metadata endpoints when "
    "the higher-level helpers don't expose what they need. "
    "Still blocked: composite, async-queries, actions/custom endpoints."
))
def sf_rest_api(
    method: str = Field(description="HTTP method: GET, POST, PATCH, DELETE"),
    path: str = Field(description="API path starting with / (e.g., /services/data/v63.0/sobjects/MarketSegment)"),
    body: str = Field(default="", description="Optional JSON request body for POST/PATCH"),
) -> dict:
    """Execute a Salesforce REST API call (restricted to safe path prefixes)."""
    if not _is_path_allowed(path):
        return {"error": f"Path not allowed: {path}. Only /services/data/ and /services/connect/ are permitted (excluding composite, async-queries, actions/custom)."}
    try:
        import re as _re
        import requests as req
        base_url = oauth_session.get_instance_url()
        token = oauth_session.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        url = f"{base_url}{path}"
        parsed_body = json.loads(body) if body.strip() else None
        if method.upper() == "GET":
            resp = req.get(url, headers=headers, timeout=60)
        elif method.upper() == "POST":
            resp = req.post(url, json=parsed_body, headers=headers, timeout=120)
        elif method.upper() == "PATCH":
            resp = req.patch(url, json=parsed_body, headers=headers, timeout=120)
        elif method.upper() == "DELETE":
            resp = req.delete(url, headers=headers, timeout=120)
        else:
            return {"error": f"Unsupported method: {method}"}
        result = {"status_code": resp.status_code}
        try:
            result["body"] = resp.json()
        except Exception:
            result["body"] = resp.text[:2000]
        return result
    except Exception as e:
        sanitized = _re.sub(r'(Bearer\s+)[A-Za-z0-9._\-]+', r'\1****', str(e))
        return {"error": sanitized}


@mcp.tool(description="Describes a Salesforce sObject to get its field metadata")
def describe_sobject(
    sobject_name: str = Field(description="The sObject API name (e.g., 'MarketSegmentDefinition', 'Account')"),
) -> dict:
    try:
        result = _describe_sobject(oauth_session, sobject_name)
        fields = result.get("fields", [])
        return [{"name": f["name"], "label": f["label"], "type": f["type"], "createable": f.get("createable")} for f in fields]
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Creates a Salesforce sObject record via the REST API")
def create_sobject_record(
    sobject_name: str = Field(description="The sObject API name (e.g., 'MarketSegmentDefinition')"),
    record: str = Field(description="JSON string with the record field values"),
) -> dict:
    try:
        parsed = json.loads(record)
        return _create_sobject_record(oauth_session, sobject_name, parsed)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Lists all data graphs defined in Data Cloud")
def list_data_graphs() -> list[dict]:
    """
    Get all data graphs.
    Data graphs define relationships between Data Model Objects for querying.
    """
    try:
        result = get_data_graphs(oauth_session)
        if isinstance(result, dict):
            return result.get("dataGraphMetadata", result.get("dataGraphs", result.get("data", [result])))
        return result
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description=(
    "Creates a Data Cloud data graph. "
    "related_objects is a JSON array where each item is "
    '{"dmo": "<DMO dev name>", '
    '"parent_field": "<field on parent DMO>", "child_field": "<field on this DMO>", '
    '"projected_fields": [<field dev names>], "related_objects": [<recursive>]}'
))
def create_data_graph(
    developer_name: str = Field(description="API name for the data graph, e.g. 'Customer360'"),
    primary_dmo: str = Field(description="Root DMO developer name, e.g. 'ssot__Individual__dlm'"),
    projected_fields: list[str] = Field(description="Field dev names to project from the primary DMO"),
    related_objects: str = Field(default="[]", description="JSON string of related objects array (see tool description)"),
    dataspace: str = Field(default="default", description="Dataspace name"),
    description: str = Field(default="", description="Optional description"),
    label: str = Field(default="", description="Optional display label"),
) -> dict:
    try:
        parsed_related = json.loads(related_objects) if related_objects else []
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON for related_objects: {e}"}
    try:
        return _create_data_graph(
            oauth_session,
            developer_name=developer_name,
            primary_dmo=primary_dmo,
            projected_fields=projected_fields,
            related_objects=parsed_related,
            dataspace=dataspace,
            description=description,
            label=label or None,
        )
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Gets metadata for all data graphs in Data Cloud, including their structure, DMOs, and relationships.")
def get_data_graphs_metadata() -> dict:
    """
    Get metadata for all data graphs.
    """
    try:
        return _get_data_graph_metadata(oauth_session)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Deletes a Data Cloud data graph by developer name")
def delete_data_graph(
    developer_name: str = Field(description="Developer name of the data graph to delete"),
) -> dict:
    try:
        return _delete_data_graph(oauth_session, developer_name)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description=(
    "Creates a Data Lake Object (DLO) in Data Cloud. A DLO is the raw landing zone for "
    "ingested data before it is mapped to a DMO.\n"
    "Required: name, label, category ('Profile', 'Engagement', or 'Other'), and fields "
    "(array of field definitions with name, label, dataType, isPrimaryKey).\n"
    "Optional: dataspaceInfo (array with dataspace name and optional filter conditions), "
    "orgUnitIdentifierFieldName, recordModifiedFieldName.\n"
    "Supported field dataTypes: Text, Number, DateTime."
))
def create_dlo(
    name: str = Field(description="DLO name (e.g. 'DataLakeObjectTwo')"),
    label: str = Field(description="Display label (e.g. 'DataLakeObjectTwo')"),
    category: str = Field(description="Category: 'Profile', 'Engagement', or 'Other'"),
    fields: str = Field(
        description=(
            "JSON array of field definitions. Each needs: name, label, "
            "dataType ('Text', 'Number', or 'DateTime'), isPrimaryKey ('true'/'false'). "
            'Example: [{"name": "FieldOne", "label": "FieldOne", "dataType": "Text", "isPrimaryKey": "true"}, '
            '{"name": "FieldTwo", "label": "FieldTwo", "dataType": "Number", "isPrimaryKey": "false"}]'
        )),
    dataspace_info: str = Field(
        default="",
        description=(
            "Optional JSON array of dataspace configurations. Each needs: name (dataspace name), "
            "and optionally filter (with conjunctiveOperator and conditions). "
            'Example: [{"name": "default"}]'
        )),
    org_unit_identifier_field: str = Field(default="", description="Optional org unit identifier field name"),
    record_modified_field: str = Field(default="", description="Optional record modified field name"),
) -> dict:
    """
    Create a Data Lake Object (DLO) in Data Cloud.
    """
    try:
        parsed_fields = json.loads(fields)
        payload = {
            "name": name,
            "label": label,
            "category": category,
            "dataLakeFieldInputRepresentations": parsed_fields,
            "orgUnitIdentifierFieldName": org_unit_identifier_field,
            "recordModifiedFieldName": record_modified_field,
        }
        if dataspace_info and dataspace_info.strip():
            payload["dataspaceInfo"] = json.loads(dataspace_info)
        return _create_data_lake_object(oauth_session, payload)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description=(
    "Updates an existing Data Lake Object (DLO) by record ID or developer name. "
    "Can update the label and/or add new fields. Only include fields you want to change."
))
def update_dlo(
    dlo_identifier: str = Field(description="DLO record ID or developer name (e.g. 'DataLakeObjectTwo__dll')"),
    label: str = Field(default="", description="Optional new display label"),
    fields: str = Field(
        default="",
        description=(
            "Optional JSON array of new field definitions to add. Each needs: "
            "name, label, dataType ('Text', 'Number', or 'DateTime'), isPrimaryKey ('true'/'false'). "
            'Example: [{"name": "FieldFour", "label": "FieldFour", "dataType": "Text", "isPrimaryKey": "false"}]'
        )),
) -> dict:
    """
    Update a Data Lake Object (DLO) — change its label or add new fields.
    """
    try:
        payload = {}
        if label:
            payload["label"] = label
        if fields and fields.strip():
            payload["dataLakeFieldInputRepresentations"] = json.loads(fields)
        if not payload:
            return {"error": "Nothing to update — provide at least label or fields"}
        return _update_data_lake_object(oauth_session, dlo_identifier, payload)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in fields: {e}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Deletes a Data Lake Object (DLO) by record ID or developer name. WARNING: This permanently removes the DLO.")
def delete_dlo(
    dlo_identifier: str = Field(description="DLO record ID or developer name (e.g. 'DataLakeObjectTwo__dll')"),
) -> dict:
    """
    Delete a Data Lake Object (DLO) from Data Cloud.
    """
    try:
        return _delete_data_lake_object(oauth_session, dlo_identifier)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Lists all data spaces configured in Data Cloud.")
def list_data_spaces() -> list[dict]:
    """
    Get all data spaces.
    """
    try:
        result = _get_data_spaces(oauth_session)
        if isinstance(result, dict):
            return result.get("dataSpaces", result.get("data", [result]))
        return result
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description="Gets details of a specific data space by its ID or name.")
def get_data_space(
    id_or_name: str = Field(description="The data space ID or name (e.g. 'default')"),
) -> dict:
    """
    Get details of a specific data space.
    """
    try:
        return _get_data_space_by_id(oauth_session, id_or_name)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Updates a data space by ID or name. Can update label and/or description.")
def update_data_space(
    id_or_name: str = Field(description="The data space ID or name (e.g. 'default')"),
    label: str = Field(default="", description="New display label"),
    description: str = Field(default="", description="New description"),
) -> dict:
    """
    Update a data space's label and/or description.
    """
    try:
        payload = {}
        if label:
            payload["label"] = label
        if description:
            payload["description"] = description
        if not payload:
            return {"error": "Nothing to update — provide at least label or description"}
        return _update_data_space(oauth_session, id_or_name, payload)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Lists all members (DMOs, DLOs, etc.) belonging to a specific data space.")
def list_data_space_members(
    id_or_name: str = Field(description="The data space ID or name (e.g. 'default')"),
) -> list[dict]:
    """
    Get all members of a data space.
    """
    try:
        result = _get_data_space_members(oauth_session, id_or_name)
        if isinstance(result, dict):
            return result.get("members", result.get("data", [result]))
        return result
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description="Gets details of a specific member within a data space by its object name.")
def get_data_space_member(
    id_or_name: str = Field(description="The data space ID or name (e.g. 'default')"),
    member_object_name: str = Field(description="The member object name (e.g. 'ssot__Individual__dlm')"),
) -> dict:
    """
    Get details of a specific member in a data space.
    """
    try:
        return _get_data_space_member(oauth_session, id_or_name, member_object_name)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description=(
    "Creates a data transform in Data Cloud. Supports two types:\n"
    "1. BATCH (type='STL') — node-based transform with load/output nodes and field mappings.\n"
    "2. STREAMING (type='SQL') — SQL-based real-time transform with a target DLO.\n\n"
    "For BATCH: definition needs type='STL', version, and nodes (LOAD_DATASET/OUTPUT with "
    "dataset, fields, fieldsMappings).\n"
    "For STREAMING: definition needs type='SQL', version, expression (SQL query), and targetDlo."
))
def create_data_transform(
    name: str = Field(description="API name for the transform (e.g. 'BatchAccountCleaning')"),
    label: str = Field(description="Display label (e.g. 'Batch Account Cleaning')"),
    transform_type: str = Field(description="Transform type: 'BATCH' or 'STREAMING'"),
    definition: str = Field(
        description=(
            "JSON string with the transform definition. Structure depends on type:\n"
            "BATCH: {\"type\": \"STL\", \"version\": \"56.0\", \"nodes\": {\"LOAD_DATASET0\": "
            "{\"action\": \"load\", \"parameters\": {\"dataset\": {\"name\": \"...__dll\", "
            "\"type\": \"dataLakeObject\"}, \"fields\": [\"...\"]}, \"sources\": []}, "
            "\"OUTPUT0\": {\"action\": \"outputD360\", \"parameters\": {\"fieldsMappings\": "
            "[{\"sourceField\": \"...\", \"targetField\": \"...\"}], \"name\": \"...__dll\", "
            "\"type\": \"dataLakeObject\"}, \"sources\": [\"LOAD_DATASET0\"]}}}\n"
            "STREAMING: {\"type\": \"SQL\", \"version\": \"63.0\", "
            "\"expression\": \"SELECT ... FROM ...\", \"targetDlo\": \"...__dll\"}"
        )),
) -> dict:
    """
    Create a data transform (BATCH or STREAMING) in Data Cloud.
    """
    try:
        parsed_definition = json.loads(definition)
        payload = {
            "name": name,
            "label": label,
            "type": transform_type,
            "definition": parsed_definition,
        }
        return _create_data_transform(oauth_session, payload)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in definition: {e}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description=(
    "Updates a data transform by name or ID (full replacement via PUT). "
    "The payload must include the complete transform definition. "
    "Fields: name, label, type ('BATCH' or 'STREAMING'), definition (with type, version, "
    "nodes/expression), and optionally creationType, currencyIsoCode, dataSpaceName, "
    "description, primarySource."
))
def update_data_transform(
    name_or_id: str = Field(description="The data transform name or ID"),
    payload: str = Field(
        description=(
            "JSON string with the full updated transform definition. Must include: "
            "name, label, type ('BATCH'/'STREAMING'), definition (with type, version, nodes/expression). "
            "Optional: creationType, currencyIsoCode, dataSpaceName, description, primarySource."
        )),
) -> dict:
    """
    Update a data transform (full replacement).
    """
    try:
        parsed = json.loads(payload)
        return _update_data_transform(oauth_session, name_or_id, parsed)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in payload: {e}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Deletes a data transform by name or ID. WARNING: This permanently removes the transform.")
def delete_data_transform(
    name_or_id: str = Field(description="The data transform name or ID to delete"),
) -> dict:
    """
    Delete a data transform from Data Cloud.
    """
    try:
        return _delete_data_transform(oauth_session, name_or_id)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Gets the run history for a specific data transform, including past execution statuses and timestamps.")
def get_data_transform_run_history(
    name_or_id: str = Field(description="The data transform name or ID"),
) -> dict:
    """
    Get run history for a data transform.
    """
    try:
        return _get_data_transform_run_history(oauth_session, name_or_id)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description="Triggers a refresh for a specific data stream to pull latest data")
def refresh_stream(
    data_stream_name: str = Field(description="The API name of the data stream to refresh"),
) -> dict:
    """
    Trigger a refresh for a data stream.
    This will pull the latest data from the source.
    """
    try:
        return refresh_data_stream(oauth_session, data_stream_name)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description=(
    "Creates a new data stream in Data Cloud. Supports three modes:\n"
    "1. CRM (SalesforceDotCom): provide connector_name + source_object.\n"
    "2. File-based (AwsS3, GCS, AzureBlob, SFTP): provide connector_name, file_name, "
    "and fields (full schema). Uses 'DataConnector' internally.\n"
    "3. IngestApi: schema-only stream for push-based ingestion.\n\n"
    "For file-based connectors, 'fields' is REQUIRED — a JSON array of objects with "
    "keys: name (target DLO API name), label (source column name), dataType (Text/Number/DateTime), "
    "isPrimaryKey (bool).\n"
    "For Engagement category, 'event_time_field' is REQUIRED.\n"
    "Use 'list_connectors' first to discover available connector names."
))
def create_new_data_stream(
    stream_name: str = Field(
        description="The name for the data stream (e.g., 'S3_Orders_Data', 'Lead_Home')"),
    connector_type: str = Field(
        description=(
            "The connector type: 'SalesforceDotCom' (CRM), 'AwsS3' (Amazon S3), "
            "'GCS' (Google Cloud Storage), 'AzureBlob' (Azure Blob Storage), "
            "'SFTP' (Secure FTP), or 'IngestApi' (push-based ingestion)"
        )),
    connector_name: str = Field(
        default="",
        description=(
            "The connector instance name (e.g., 'SalesforceDotCom_Home', 'test'). "
            "Required for all types except IngestApi."
        )),
    source_object: str = Field(
        default="",
        description=(
            "For SalesforceDotCom only: the CRM object API name (e.g., 'Lead', 'Account'). "
            "Not used for file-based connectors (use file_name instead)."
        )),
    category: str = Field(
        default="Profile",
        description="Object category: 'Profile', 'Engagement', or 'Other'"),
    fields: str = Field(
        default="",
        description=(
            "JSON array of field definitions. REQUIRED for file-based and IngestApi connectors. "
            "Each object: {\"name\": \"order_id__c\", \"label\": \"order_id\", "
            "\"dataType\": \"Text\", \"isPrimaryKey\": true}. "
            "dataType must be Text, Number, or DateTime."
        )),
    file_name: str = Field(
        default="",
        description=(
            "For file-based connectors: the file name or pattern to ingest "
            "(e.g., 'orders.csv', 'customer_profile.csv', '*.parquet'). "
            "Required for AwsS3/GCS/AzureBlob/SFTP."
        )),
    file_type: str = Field(
        default="CSV",
        description="File format: 'CSV' or 'PARQUET' (default: CSV)"),
    import_directory: str = Field(
        default="/",
        description=(
            "Directory path within the bucket/container. "
            "Use '/' for root, or a subfolder like 'data/orders/'. Default: '/'"
        )),
    frequency_type: str = Field(
        default="DAILY",
        description="Refresh frequency: 'HOURLY', 'DAILY', 'WEEKLY', or 'MONTHLY'"),
    frequency_hours: str = Field(
        default="",
        description=(
            "JSON array of hours (0-23) for DAILY/WEEKLY/MONTHLY schedules. "
            "E.g., '[7]' for 7am, '[9,15]' for 9am and 3pm. Not used for HOURLY."
        )),
    frequency_day_of_week: str = Field(
        default="",
        description="Day of week for WEEKLY frequency (e.g., 'Monday', 'Wednesday'). Case-sensitive."),
    event_time_field: str = Field(
        default="",
        description=(
            "REQUIRED for Engagement category: the target field name (DLO API name) "
            "that holds the event timestamp (e.g., 'created_at__c', 'event_timestamp__c'). "
            "Must be a DateTime field."
        )),
    dll_name: str = Field(
        default="",
        description=(
            "Optional: custom DLO API name (e.g., 'S3_Orders__dll'). "
            "Auto-generated as '{stream_name}__dll' if not provided."
        )),
    data_space: str = Field(
        default="default",
        description="The data space to deploy to"),
    refresh_mode: str = Field(
        default="UPSERT",
        description="Refresh mode: 'UPSERT' (incremental) or 'OVERWRITE' (full replace)"),
) -> dict:
    """
    Create a new data stream to ingest data from any supported connector into Data Cloud.
    """
    try:
        parsed_fields = None
        if fields and fields.strip():
            parsed_fields = json.loads(fields)

        parsed_hours = None
        if frequency_hours and frequency_hours.strip():
            parsed_hours = json.loads(frequency_hours)

        result = create_data_stream(
            oauth_session,
            name=stream_name,
            connector_type=connector_type,
            connector_name=connector_name or None,
            source_object=source_object or None,
            category=category,
            data_space=data_space,
            refresh_mode=refresh_mode,
            fields=parsed_fields,
            file_name=file_name or None,
            file_type=file_type,
            import_directory=import_directory,
            frequency_type=frequency_type,
            frequency_hours=parsed_hours,
            frequency_day_of_week=frequency_day_of_week or None,
            event_time_field=event_time_field or None,
            dll_name=dll_name or None,
        )
        return {
            "status": "created",
            "dataStream": stream_name,
            "connectorType": connector_type,
            "connector": connector_name,
            "category": category,
            "details": result,
        }
    except Exception as e:
        return {
            "error": str(e),
            "dataStream": stream_name,
            "connectorType": connector_type,
            "connector": connector_name,
        }


@mcp.tool(description=(
    "Creates a schema for an Ingestion API data stream. "
    "Use this as the first step when setting up an IngestApi connector: "
    "define the schema (fields and types), then push data via the Bulk or Streaming Ingestion API."
))
def create_ingestion_schema(
    object_name: str = Field(
        description="The DLO object name for the ingestion target (e.g., 'MyCustomOrders')"),
    fields: str = Field(
        description=(
            'JSON array of field definitions. Each field needs "name" and "type". '
            'Supported types: TEXT, NUMBER, DATE, DATETIME, BOOLEAN. '
            'Example: [{"name": "Id", "type": "TEXT"}, {"name": "Amount", "type": "NUMBER"}, '
            '{"name": "OrderDate", "type": "DATETIME"}]'
        )),
    primary_key: str = Field(
        default="Id",
        description="The primary key field name (default: 'Id')"),
) -> dict:
    """
    Create or update the schema for an Ingestion API data stream.
    After schema creation, data can be pushed via the Ingestion API endpoints.
    """
    try:
        parsed_fields = json.loads(fields)
        result = create_ingestion_api_schema(
            oauth_session,
            object_name=object_name,
            fields=parsed_fields,
            primary_key=primary_key,
        )
        return result
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in fields parameter: {e}"}
    except Exception as e:
        return {"error": str(e), "object": object_name}


@mcp.tool(description=(
    "Lists all data source connectors configured in the org. "
    "Returns connector names, types, and status. Use this to discover available connectors "
    "before creating data streams (e.g., SalesforceDotCom_Home, My_S3_Connector, etc.)."
))
def list_available_connectors() -> list[dict]:
    """
    List all connectors configured in the org.
    Helps discover connector names and types for use with create_new_data_stream.
    """
    try:
        result = _list_connectors(oauth_session)
        if isinstance(result, dict):
            return result.get("dataConnectors", result.get("data", [result]))
        return result
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description=(
    "Lists available source objects for a specific connector. "
    "Use this to discover which objects/files/tables can be ingested from a connector "
    "before creating a data stream."
))
def list_connector_objects(
    connector_name: str = Field(
        description="The connector name (e.g., 'SalesforceDotCom_Home', 'My_S3_Connector')"),
) -> list[dict]:
    """
    List source objects available in a connector.
    """
    try:
        result = _get_connector_source_objects(oauth_session, connector_name)
        if isinstance(result, dict):
            return result.get("sourceObjects", result.get("data", [result]))
        return result
    except Exception as e:
        return [{"error": str(e), "connector": connector_name}]


@mcp.tool(description="Deletes a data stream from Data Cloud. Optionally deletes the underlying Data Lake Object too.")
def delete_stream(
    data_stream_name: str = Field(
        description="The name of the data stream to delete (e.g., 'Lead_Home')"),
    delete_data_lake_object: bool = Field(
        default=True,
        description="Whether to also delete the underlying Data Lake Object (default: true)"),
) -> dict:
    """
    Delete a data stream from Data Cloud.
    WARNING: This permanently removes the data stream and optionally its data.
    """
    try:
        return delete_data_stream(oauth_session, data_stream_name, delete_data_lake_object)
    except Exception as e:
        return {"error": str(e), "dataStream": data_stream_name}


@mcp.tool(description=(
    "Lists all Data Cloud retrievers (including system retrievers like "
    "SalesforceHelpContentRetriever, DynamicRetriever, WebRetrievalAction, and "
    "any custom retrievers built on search indexes). Returns name, label, "
    "source DMO, vector DMO, search type, and active configuration."
))
def list_retrievers() -> list[dict]:
    try:
        result = get_retrievers(oauth_session)
        if isinstance(result, dict):
            return result.get("retrievers", [result])
        return result
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description=(
    "Lists all Data Cloud search indexes (semantic search definitions). "
    "Returns each index's developer name, label, source DMO, chunk DMO, "
    "and chunking configuration."
))
def list_search_indexes() -> list[dict]:
    try:
        result = get_search_indexes(oauth_session)
        if isinstance(result, dict):
            return result.get("semanticSearchDefinitionDetails", [result])
        return result
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool(description="Lists source objects already connected for a given connector. "
          "Helps users see which objects are already ingested before creating new data streams.")
def list_connected_source_objects(
    connector_name: str = Field(
        default="SalesforceDotCom_Home",
        description="The connector name to check (default: 'SalesforceDotCom_Home')"),
) -> list[str]:
    """
    List source objects that already have data streams for a given connector.
    Useful to avoid creating duplicate streams.
    """
    try:
        return list_connector_source_objects(oauth_session, connector_name)
    except Exception as e:
        return [f"error: {str(e)}"]


@mcp.tool(description=(
    "Creates a fully custom Data Model Object (DMO) in Data Cloud. "
    "Use this when the target DMO doesn't exist yet — e.g., for custom entities like "
    "'CustomerOrders', 'ProductReviews', etc. The API auto-adds system fields "
    "(DataSource, DataSourceObject, InternalOrganization) and Key Qualifier fields. "
    "Supported categories: Profile, Engagement, Other. "
    "Supported field types: Text, Number, DateTime. "
    "After creation, use create_dlo_dmo_mapping to map a DLO to the new DMO."
))
def create_custom_dmo(
    name: str = Field(
        description="API name for the DMO (alphanumeric + underscores, must start with a letter, "
                    "must NOT start with 'ssot'). The API appends '__dlm' automatically. "
                    "Example: 'CustomerOrders'"),
    label: str = Field(
        description="Human-readable display label. Example: 'Customer Orders'"),
    category: str = Field(
        description="DMO category: 'Profile', 'Engagement', or 'Other'"),
    fields: str = Field(
        description=(
            "JSON array of field definitions. Each element must have: "
            "'name' (API name, no __c suffix needed), 'label' (display label), "
            "'dataType' ('Text', 'Number', or 'DateTime'), "
            "'isPrimaryKey' (true/false). At least one field must be a primary key. "
            'Example: [{"name":"OrderId","label":"Order Id","dataType":"Text","isPrimaryKey":true},'
            '{"name":"Amount","label":"Amount","dataType":"Number","isPrimaryKey":false}]'
        )),
) -> dict:
    try:
        parsed = json.loads(fields)
        if not isinstance(parsed, list) or not parsed:
            return {"error": "fields must be a non-empty JSON array"}
        has_pk = False
        for f in parsed:
            if "name" not in f or "label" not in f or "dataType" not in f:
                return {
                    "error": "Each field must have 'name', 'label', and 'dataType'",
                    "invalid_entry": f,
                }
            if f.get("isPrimaryKey"):
                has_pk = True
        if not has_pk:
            return {"error": "At least one field must have 'isPrimaryKey': true"}
        if category not in ("Profile", "Engagement", "Other"):
            return {"error": f"Invalid category '{category}'. Must be 'Profile', 'Engagement', or 'Other'"}
        return _create_custom_dmo(oauth_session, name, label, category, parsed)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in fields: {e}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description=(
    "Creates one or more custom fields on a Data Model Object (DMO) via the Tooling API. "
    "Idempotent: if a field already exists, it ensures it is properly registered as a DMO field. "
    "Note: create_dlo_dmo_mapping auto-creates missing custom fields, so you often don't need to call this separately. "
    "This tool uses the Tooling API: POST /tooling/sobjects/CustomField + POST /tooling/sobjects/MktDataModelField."
))
def create_custom_dmo_fields(
    dmo_name: str = Field(
        description="DMO API name (e.g., 'ssot__Individual__dlm')"),
    fields: str = Field(
        description=(
            "JSON array of field definitions to create. Each element needs: "
            "'name' (API name ending in __c, e.g. 'Email_Address__c'), "
            "'label' (display label, e.g. 'Email Address'), and optionally "
            "'type' (default: 'Text'; valid: Text, Number, Currency, Percent, "
            "Date, DateTime, Checkbox, etc.), "
            "'length' (default: 255, for Text fields only), "
            "'precision' (total digits, for Number/Currency/Percent; default 18), and "
            "'scale' (digits after decimal, for Number/Currency/Percent; default 0 — "
            "use 2+ for decimal/currency amounts). "
            'Examples: [{"name": "Email_Address__c", "label": "Email Address"}, '
            '{"name": "Loyalty_Points__c", "label": "Loyalty Points", "type": "Number", "precision": 18, "scale": 0}, '
            '{"name": "Order_Amount__c", "label": "Order Amount", "type": "Currency", "precision": 18, "scale": 2}]'
        )),
) -> dict:
    try:
        parsed = json.loads(fields)
        if not isinstance(parsed, list) or not parsed:
            return {"error": "fields must be a non-empty JSON array"}
        results = []
        for f in parsed:
            if "name" not in f or "label" not in f:
                results.append({"error": "Each field must have 'name' and 'label'", "field": f})
                continue
            result = _create_custom_dmo_field(
                oauth_session,
                dmo_name=dmo_name,
                field_name=f["name"],
                field_label=f["label"],
                field_type=f.get("type", "Text"),
                field_length=f.get("length", 255),
                precision=f.get("precision"),
                scale=f.get("scale"),
            )
            results.append(result)
        created = [r for r in results if r.get("status") == "created"]
        failed = [r for r in results if "error" in r]
        return {
            "dmo_name": dmo_name,
            "total": len(parsed),
            "created": len(created),
            "failed": len(failed),
            "results": results,
        }
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in fields: {e}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description=(
    "Creates a DLO-to-DMO mapping in Data Cloud. Maps a Data Lake Object (source) "
    "to a Data Model Object (target) with field-level mappings. "
    "Runs pre-flight validation against live DLO/DMO metadata: auto-injects the DLO PK "
    "-> ssot__Id__c, auto-injects an event-timestamp mapping for Engagement-category "
    "DLOs, and refuses Reference targets / type mismatches with clear errors and fuzzy "
    "suggestions. Set dry_run=true to validate without writing. Set auto_fix=false to "
    "disable PK/timestamp injection. "
    "Automatically creates any missing __c custom fields on the target DMO before mapping. "
    "Use list_data_streams to find DLO names and list_data_model_objects / get_dmo_details "
    "to find DMO names and their fields."
))
def create_dlo_dmo_mapping(
    source_entity: str = Field(
        description="DLO developer name — the source entity (e.g., 'test1__dll')"),
    target_entity: str = Field(
        description="DMO developer name — the target entity (e.g., 'ssot__AcademicYear__dlm')"),
    field_mapping: str = Field(
        description=(
            "JSON array of field mappings. Each element must have "
            "'sourceFieldDeveloperName' (DLO field, usually ending in __c) and "
            "'targetFieldDeveloperName' (DMO field). "
            "PK and engagement-timestamp mappings are auto-injected when missing "
            "(disable with auto_fix=false). "
            'Example: [{"sourceFieldDeveloperName": "email__c", '
            '"targetFieldDeveloperName": "ssot__Id__c"}]'
        )),
    dry_run: bool = Field(
        default=False,
        description=(
            "If true, runs pre-flight validation only and returns the report "
            "(plus the would-be payload) without creating the mapping."
        )),
    auto_fix: bool = Field(
        default=True,
        description=(
            "If true (default), auto-injects the DLO primary-key -> ssot__Id__c mapping, "
            "and for Engagement DLOs the event-timestamp mapping. "
            "Set to false to submit the payload exactly as provided."
        )),
) -> dict:
    try:
        parsed = json.loads(field_mapping)
        if not isinstance(parsed, list) or not parsed:
            return {"error": "field_mapping must be a non-empty JSON array"}
        for fm in parsed:
            if "sourceFieldDeveloperName" not in fm or "targetFieldDeveloperName" not in fm:
                return {
                    "error": "Each field mapping must have 'sourceFieldDeveloperName' and 'targetFieldDeveloperName'",
                    "invalid_entry": fm,
                }

        fixed, report = _validate_and_fix_mapping(
            source_entity, target_entity, parsed, auto_fix=auto_fix,
        )

        if report["errors"]:
            return {
                "status": "validation_failed",
                "report": report,
                "draft_payload": fixed,
            }

        if dry_run:
            return {
                "status": "would_succeed",
                "report": report,
                "draft_payload": fixed,
            }

        result = _create_dlo_dmo_mapping(oauth_session, source_entity, target_entity, fixed)
        if isinstance(result, dict):
            result["preflight_report"] = report
        return result
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in field_mapping: {e}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description=(
    "Updates an existing DLO-to-DMO mapping with a new set of field mappings. "
    "Fetches the current mapping, computes a diff (added/removed fields), then "
    "deletes and recreates the mapping atomically. Automatically creates any "
    "missing custom fields on the target DMO. Provide the mapping_name "
    "(returned when the mapping was created, e.g., 'S3_Customer_Info_map_Individual_1778669048328') "
    "and the new complete list of field mappings."
))
def update_dlo_dmo_mapping(
    mapping_name: str = Field(
        description="The existing mapping's developerName "
                    "(e.g., 'S3_Customer_Info_map_Individual_1778669048328')"),
    field_mapping: str = Field(
        description=(
            "JSON array of the NEW complete field mappings. Each element must have "
            "'sourceFieldDeveloperName' (DLO field) and 'targetFieldDeveloperName' (DMO field). "
            "System fields (DataSource, InternalOrganization, KQ_) are auto-added by the API. "
            'Example: [{"sourceFieldDeveloperName": "email__c", '
            '"targetFieldDeveloperName": "ssot__Id__c"}]'
        )),
) -> dict:
    try:
        parsed = json.loads(field_mapping)
        if not isinstance(parsed, list) or not parsed:
            return {"error": "field_mapping must be a non-empty JSON array"}
        for fm in parsed:
            if "sourceFieldDeveloperName" not in fm or "targetFieldDeveloperName" not in fm:
                return {
                    "error": "Each field mapping must have 'sourceFieldDeveloperName' and 'targetFieldDeveloperName'",
                    "invalid_entry": fm,
                }
        return _update_dlo_dmo_mapping(oauth_session, mapping_name, parsed)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in field_mapping: {e}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description=(
    "Deletes custom fields from a Data Model Object (DMO). "
    "Queries the Tooling API for MktDataModelField records matching the given field names, "
    "then deletes each MktDataModelField and its backing CustomField definition. "
    "Use get_dmo_details to find custom fields (creationType='Custom') before calling this."
))
def delete_custom_dmo_fields(
    dmo_name: str = Field(
        description="DMO API name (e.g., 'ssot__Individual__dlm')"),
    field_names: str = Field(
        description=(
            "JSON array of field API names to delete (ending in __c). "
            'Example: ["Email_Address__c", "Phone_Number__c"]'
        )),
) -> dict:
    try:
        parsed = json.loads(field_names)
        if not isinstance(parsed, list) or not parsed:
            return {"error": "field_names must be a non-empty JSON array of strings"}
        return _delete_custom_dmo_fields(oauth_session, dmo_name, parsed)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in field_names: {e}"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool(description=(
    "Deletes a DLO-to-DMO mapping. You can specify EITHER the mapping_name directly, "
    "OR provide both source_entity (DLO) and target_entity (DMO) to look it up automatically. "
    "The mapping name is returned when you create a mapping, or you can find it "
    "via get_data_stream_mappings."
))
def delete_dlo_dmo_mapping(
    mapping_name: str = Field(
        default="",
        description="The mapping name to delete (e.g., 'S3_Customer_Info_map_Individual_1778666104025'). "
                    "Leave empty if providing source_entity and target_entity instead."),
    source_entity: str = Field(
        default="",
        description="DLO developer name (e.g., 'S3_Customer_Info__dll'). "
                    "Used with target_entity to look up the mapping name."),
    target_entity: str = Field(
        default="",
        description="DMO developer name (e.g., 'ssot__Individual__dlm'). "
                    "Used with source_entity to look up the mapping name."),
) -> dict:
    try:
        return _delete_dlo_dmo_mapping(
            oauth_session,
            mapping_name=mapping_name or None,
            source_entity=source_entity or None,
            target_entity=target_entity or None,
        )
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Pre-flight validation, auto-fix, and metadata cache for DLO->DMO mappings.
#
# Salesforce only validates a mapping at execute time and its error messages
# are notoriously poor (NPE on Reference targets, MISSING_ARGUMENT for omitted
# PKs, ORA-30006 on concurrent writes to the same DLO). Catching these
# upstream — once, in the server — collapses the iterative-debugging loop
# that otherwise dominates wall time.
# ---------------------------------------------------------------------------

METADATA_CACHE_TTL_S = 60
_METADATA_CACHE: dict = {}
_METADATA_CACHE_LOCK = threading.Lock()


def _cache_get(key: str):
    with _METADATA_CACHE_LOCK:
        entry = _METADATA_CACHE.get(key)
        if entry and (time.time() - entry["t"]) < METADATA_CACHE_TTL_S:
            return entry["v"]
        return None


def _cache_set(key: str, value) -> None:
    with _METADATA_CACHE_LOCK:
        _METADATA_CACHE[key] = {"t": time.time(), "v": value}


def _normalize_type(t) -> str:
    """Collapse SSOT/Tooling/Salesforce type names to a small canonical set."""
    if not t:
        return "Unknown"
    s = str(t).strip().upper()
    if s in ("STRING", "TEXT", "VARCHAR", "EMAIL", "PHONE", "URL", "TEXTAREA"):
        return "Text"
    if s in ("NUMBER", "DOUBLE", "DECIMAL", "INTEGER", "INT", "LONG",
             "CURRENCY", "PERCENT", "FLOAT"):
        return "Number"
    if s in ("DATE",):
        return "Date"
    if s in ("DATETIME", "TIMESTAMP"):
        return "DateTime"
    if s in ("BOOLEAN", "BOOL", "CHECKBOX"):
        return "Boolean"
    if s in ("REFERENCE", "LOOKUP", "MASTERDETAIL", "MASTER_DETAIL"):
        return "Reference"
    return s.title()


def _add_field_with_aliases(fields_map: dict, fname: str, meta: dict) -> None:
    """
    Insert a field under both its bare and __c-suffixed name.

    The SSOT data-streams API returns DLO field names without __c suffix
    (e.g. 'loyalty_id'), while the SSOT mapping API and most callers use
    the __c form ('loyalty_id__c'). Treat them as equivalent on lookup.
    """
    fields_map[fname] = meta
    if fname.endswith("__c"):
        bare = fname[:-3]
        fields_map.setdefault(bare, meta)
    else:
        fields_map.setdefault(f"{fname}__c", meta)


def _canonical_field(name: str) -> str:
    """Return the __c-suffixed canonical form used by the mapping API."""
    if name.endswith("__c"):
        return name
    return f"{name}__c"


def _types_compatible(src_type: str, tgt_type: str) -> bool:
    """Whether a DLO source type can be mapped onto a DMO target type."""
    if src_type == tgt_type:
        return True
    if src_type == "Unknown" or tgt_type == "Unknown":
        # Don't block when we can't tell — Salesforce will give the final word.
        return True
    # Lossless widenings.
    if src_type == "Date" and tgt_type == "DateTime":
        return True
    # Number / Boolean / Date can be stored as Text; common in practice.
    if tgt_type == "Text" and src_type in ("Number", "Boolean", "Date", "DateTime"):
        return True
    return False


def _get_dlo_metadata(dlo_name: str) -> dict:
    """Fetch and normalize DLO metadata. Cached for METADATA_CACHE_TTL_S seconds."""
    cached = _cache_get(f"dlo:{dlo_name}")
    if cached is not None:
        return cached

    raw = get_data_stream_details(oauth_session, dlo_name)
    info = raw.get("dataLakeObjectInfo") or raw.get("dataLakeObject") or {}
    fields_raw = (
        info.get("dataLakeFieldInputRepresentations")
        or info.get("fields")
        or raw.get("fields")
        or []
    )

    fields: dict = {}
    pk_field = None
    for f in fields_raw:
        fname = f.get("name") or f.get("developerName")
        if not fname:
            continue
        is_pk = bool(f.get("isPrimaryKey") or f.get("primaryKey"))
        meta = {
            "name": fname,
            "type": _normalize_type(f.get("dataType") or f.get("type")),
            "is_pk": is_pk,
        }
        _add_field_with_aliases(fields, fname, meta)
        if is_pk and pk_field is None:
            pk_field = _canonical_field(fname)

    norm = {
        "name": dlo_name,
        "category": info.get("category") or raw.get("category"),
        "fields": fields,
        "pk_field": pk_field,
        "event_field": (
            info.get("eventDateTimeFieldName")
            or raw.get("eventDateTimeFieldName")
        ),
    }
    _cache_set(f"dlo:{dlo_name}", norm)
    return norm


def _get_dmo_metadata(dmo_name: str) -> dict:
    """Fetch and normalize DMO metadata. Cached for METADATA_CACHE_TTL_S seconds."""
    cached = _cache_get(f"dmo:{dmo_name}")
    if cached is not None:
        return cached

    raw = get_data_model_object_details(oauth_session, dmo_name)
    fields_raw = raw.get("fields") or []
    fields: dict = {}
    for f in fields_raw:
        fname = f.get("name") or f.get("developerName")
        if not fname:
            continue
        meta = {
            "name": fname,
            "type": _normalize_type(f.get("dataType") or f.get("type")),
            "reference_to": f.get("referenceTo") or f.get("relatedDmoName") or [],
        }
        _add_field_with_aliases(fields, fname, meta)

    norm = {
        "name": dmo_name,
        "category": raw.get("category"),
        "fields": fields,
    }
    _cache_set(f"dmo:{dmo_name}", norm)
    return norm


# Engagement DMO targets, ordered by preference.
_ENGAGEMENT_TIMESTAMP_TARGETS = (
    "ssot__EngagementDateTm__c",
    "ssot__OccurredDate__c",
    "ssot__CreatedDate__c",
)


def _validate_and_fix_mapping(
    source_entity: str,
    target_entity: str,
    field_mapping: list,
    auto_fix: bool = True,
) -> Tuple[list, dict]:
    """
    Pre-flight validation + optional auto-fix for a DLO->DMO mapping payload.

    Returns (possibly-modified field_mapping, report).

    Auto-fix (when enabled) injects two well-known invariants:
      1. DLO primary key -> DMO 'ssot__Id__c' (always required by SSOT).
      2. For Engagement-category DLOs: an event-timestamp mapping
         (DLO event field -> DMO ssot__EngagementDateTm__c / ssot__CreatedDate__c).

    Validation refuses (errors[]) for:
      - Unknown source field (with fuzzy-match suggestion).
      - Target field that is a Reference/Lookup type.
      - Source/target type mismatch that Salesforce can't coerce.

    Validation warns (warnings[]) for:
      - Duplicate mappings (deduped).
      - Target fields that don't exist and don't look like custom fields.
    """
    report: dict = {"auto_applied": [], "warnings": [], "errors": []}

    try:
        dlo = _get_dlo_metadata(source_entity)
    except Exception as e:
        report["warnings"].append(
            f"Could not fetch DLO metadata for '{source_entity}' ({e}); skipping pre-flight."
        )
        return field_mapping, report

    try:
        dmo = _get_dmo_metadata(target_entity)
    except Exception as e:
        report["warnings"].append(
            f"Could not fetch DMO metadata for '{target_entity}' ({e}); skipping pre-flight."
        )
        return field_mapping, report

    fixed: list = list(field_mapping)

    if auto_fix:
        # 1. Auto-inject DLO PK -> DMO PK
        already_has_dmo_pk = any(
            fm.get("targetFieldDeveloperName") == "ssot__Id__c" for fm in fixed
        )
        if dlo["pk_field"] and "ssot__Id__c" in dmo["fields"] and not already_has_dmo_pk:
            fixed.insert(0, {
                "sourceFieldDeveloperName": dlo["pk_field"],
                "targetFieldDeveloperName": "ssot__Id__c",
            })
            report["auto_applied"].append(
                f"Injected primary-key mapping: {dlo['pk_field']} -> ssot__Id__c"
            )

        # 2. Auto-inject engagement timestamp for Engagement DLOs.
        if (dlo["category"] or "").lower() == "engagement":
            already_has_event = any(
                fm.get("targetFieldDeveloperName") in _ENGAGEMENT_TIMESTAMP_TARGETS
                for fm in fixed
            )
            if not already_has_event:
                src_event = dlo["event_field"]
                if not src_event and "created_at__c" in dlo["fields"]:
                    src_event = "created_at__c"
                if src_event:
                    src_event = _canonical_field(src_event)
                tgt_event = next(
                    (t for t in _ENGAGEMENT_TIMESTAMP_TARGETS if t in dmo["fields"]),
                    None,
                )
                if src_event and tgt_event:
                    fixed.insert(0, {
                        "sourceFieldDeveloperName": src_event,
                        "targetFieldDeveloperName": tgt_event,
                    })
                    report["auto_applied"].append(
                        f"Injected engagement timestamp: {src_event} -> {tgt_event} "
                        f"(DLO category=Engagement)"
                    )
                else:
                    report["errors"].append(
                        f"DLO '{source_entity}' is Engagement category but no event "
                        f"timestamp mapping was provided and one could not be inferred. "
                        f"Tried DLO source field: {src_event or '<unknown>'}; "
                        f"tried DMO targets: {list(_ENGAGEMENT_TIMESTAMP_TARGETS)}."
                    )

    # Per-mapping validation (after auto-fix so injected entries are checked too).
    seen: set = set()
    deduped: list = []
    for fm in fixed:
        src = fm.get("sourceFieldDeveloperName")
        tgt = fm.get("targetFieldDeveloperName")
        if not src or not tgt:
            report["errors"].append(f"Mapping missing source or target: {fm}")
            continue

        key = (src, tgt)
        if key in seen:
            report["warnings"].append(f"Duplicate mapping deduped: {src} -> {tgt}")
            continue
        seen.add(key)
        deduped.append(fm)

        if src not in dlo["fields"]:
            # Build a clean candidate list: dedupe alias pairs and hide internal KQ_*.
            seen_canon: set = set()
            candidates: list = []
            for fname in dlo["fields"]:
                if fname.startswith("KQ_"):
                    continue
                canon = _canonical_field(fname)
                if canon in seen_canon:
                    continue
                seen_canon.add(canon)
                candidates.append(canon)
            suggestions = difflib.get_close_matches(
                _canonical_field(src), candidates, n=3, cutoff=0.6
            )
            msg = f"Source field '{src}' not found on DLO '{source_entity}'."
            if suggestions:
                msg += f" Did you mean: {', '.join(suggestions)}?"
            report["errors"].append(msg)
            continue

        if tgt in dmo["fields"]:
            tgt_meta = dmo["fields"][tgt]
            if tgt_meta["type"] == "Reference":
                report["errors"].append(
                    f"Target field '{tgt}' on DMO '{target_entity}' is a Reference/Lookup "
                    f"({tgt_meta.get('reference_to')}). Lookup fields can't be populated "
                    f"via DLO field mapping; configure the relationship via Identity "
                    f"Resolution or a separate setup."
                )
                continue
            src_type = dlo["fields"][src]["type"]
            if not _types_compatible(src_type, tgt_meta["type"]):
                report["errors"].append(
                    f"Type mismatch: DLO '{src}' is {src_type} but DMO target '{tgt}' is "
                    f"{tgt_meta['type']}. Map to a {src_type}-typed DMO field, or create "
                    f"one with create_custom_dmo_fields."
                )
                continue
        else:
            # Target doesn't exist yet. The downstream helper auto-creates
            # __c custom fields; only warn if it doesn't even look like one.
            if not (tgt.startswith("ssot__") or tgt.endswith("__c")):
                report["warnings"].append(
                    f"Target '{tgt}' is not on DMO '{target_entity}' and doesn't look like "
                    f"a custom field (must end in __c) — Salesforce will likely reject it."
                )

    return deduped, report


def _execute_single_mapping(
    mapping_spec: dict,
    dry_run: bool = False,
    auto_fix: bool = True,
) -> dict:
    """Execute (or dry-run) a single DLO-DMO mapping with pre-flight validation."""
    start = time.time()
    spec_id = f"{mapping_spec['source_entity']} -> {mapping_spec['target_entity']}"
    try:
        parsed_fields = json.loads(mapping_spec["field_mapping"])
        # Per-spec overrides take precedence over batch-level defaults.
        spec_dry_run = bool(mapping_spec.get("dry_run", dry_run))
        spec_auto_fix = bool(mapping_spec.get("auto_fix", auto_fix))

        fixed, report = _validate_and_fix_mapping(
            mapping_spec["source_entity"],
            mapping_spec["target_entity"],
            parsed_fields,
            auto_fix=spec_auto_fix,
        )

        if report["errors"]:
            elapsed = round(time.time() - start, 2)
            return {
                "mapping": spec_id,
                "status": "validation_failed",
                "elapsed_seconds": elapsed,
                "result": {"report": report, "draft_payload": fixed},
            }

        if spec_dry_run:
            elapsed = round(time.time() - start, 2)
            return {
                "mapping": spec_id,
                "status": "would_succeed",
                "elapsed_seconds": elapsed,
                "result": {"report": report, "draft_payload": fixed},
            }

        result = _create_dlo_dmo_mapping(
            oauth_session,
            mapping_spec["source_entity"],
            mapping_spec["target_entity"],
            fixed,
        )
        if isinstance(result, dict):
            result["preflight_report"] = report
        elapsed = round(time.time() - start, 2)
        is_error = (
            isinstance(result, dict)
            and ("error" in result or "error_status" in result)
        )
        return {
            "mapping": spec_id,
            "status": "failed" if is_error else "success",
            "elapsed_seconds": elapsed,
            "result": result,
        }
    except Exception as e:
        elapsed = round(time.time() - start, 2)
        return {
            "mapping": spec_id,
            "status": "error",
            "elapsed_seconds": elapsed,
            "result": {"error": str(e)},
        }


@mcp.tool(description=(
    "Creates multiple DLO-to-DMO mappings, grouping by source DLO so different DLOs "
    "run in parallel while mappings against the same DLO run sequentially. "
    "This avoids ORA-30006 row-lock contention that flat parallelism causes. "
    "Each spec runs through the same pre-flight validation as create_dlo_dmo_mapping "
    "(PK auto-inject, engagement-timestamp auto-inject, type/reference checks, "
    "fuzzy source-field suggestions). Set dry_run=true to validate the whole batch "
    "without writing. Per-spec 'dry_run' / 'auto_fix' overrides take precedence."
))
def batch_create_dlo_dmo_mappings(
    mappings: str = Field(
        description=(
            "JSON array of mapping specifications. Each element must have: "
            "'source_entity' (DLO developer name), 'target_entity' (DMO developer name), "
            "and 'field_mapping' (JSON string of field mappings array, same format as "
            "create_dlo_dmo_mapping). Optional per-spec keys: 'dry_run' (bool), "
            "'auto_fix' (bool). "
            'Example: [{"source_entity": "S3_Cust_Inf__dll", '
            '"target_entity": "ssot__Individual__dlm", '
            '"field_mapping": "[{\\"sourceFieldDeveloperName\\": \\"customer_id__c\\", '
            '\\"targetFieldDeveloperName\\": \\"ssot__Id__c\\"}]"}]'
        )),
    max_workers: int = Field(
        default=5,
        description=(
            "Max number of *distinct DLOs* processed in parallel (default: 5). "
            "Mappings against the same DLO are always serialized — this avoids "
            "ORA-30006 lock contention in the SSOT mapping API. "
            "Lower this if you hit org-level API rate limits."
        )),
    dry_run: bool = Field(
        default=False,
        description=(
            "Default dry_run for all specs (per-spec 'dry_run' overrides). "
            "If true, every mapping is validated without writing."
        )),
    auto_fix: bool = Field(
        default=True,
        description=(
            "Default auto_fix for all specs (per-spec 'auto_fix' overrides). "
            "If true, injects PK and engagement-timestamp mappings when missing."
        )),
) -> dict:
    try:
        specs = json.loads(mappings)
        if not isinstance(specs, list) or not specs:
            return {"error": "mappings must be a non-empty JSON array"}

        for i, spec in enumerate(specs):
            for key in ("source_entity", "target_entity", "field_mapping"):
                if key not in spec:
                    return {"error": f"Mapping at index {i} missing required key '{key}'", "spec": spec}

        # Group by source DLO. Within a group we run sequentially (avoids
        # ORA-30006 row-lock contention on the SSOT mapping API). Across
        # groups we run in parallel.
        groups: dict = defaultdict(list)
        for i, spec in enumerate(specs):
            groups[spec["source_entity"]].append((i, spec))

        def _run_group(group_specs):
            out = []
            for i, spec in group_specs:
                out.append((i, _execute_single_mapping(spec, dry_run=dry_run, auto_fix=auto_fix)))
            return out

        total_start = time.time()
        worker_count = min(max_workers, len(groups))
        all_indexed: list = []

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_to_src = {
                executor.submit(_run_group, group): src
                for src, group in groups.items()
            }
            for future in as_completed(future_to_src):
                src = future_to_src[future]
                try:
                    all_indexed.extend(future.result())
                except Exception as e:
                    # Mark every spec in this DLO group as errored.
                    for i, spec in groups[src]:
                        all_indexed.append((i, {
                            "mapping": f"{spec['source_entity']} -> {spec['target_entity']}",
                            "status": "error",
                            "elapsed_seconds": 0,
                            "result": {"error": str(e)},
                        }))

        all_indexed.sort(key=lambda x: x[0])
        ordered_results = [r[1] for r in all_indexed]

        total_elapsed = round(time.time() - total_start, 2)
        succeeded = sum(1 for r in ordered_results if r["status"] == "success")
        would_succeed = sum(1 for r in ordered_results if r["status"] == "would_succeed")
        validation_failed = sum(1 for r in ordered_results if r["status"] == "validation_failed")
        failed = sum(
            1 for r in ordered_results
            if r["status"] not in ("success", "would_succeed")
        )

        return {
            "summary": {
                "total": len(specs),
                "succeeded": succeeded,
                "would_succeed": would_succeed,
                "validation_failed": validation_failed,
                "failed": failed,
                "total_elapsed_seconds": total_elapsed,
                "execution_mode": "group-by-dlo (parallel across DLOs, serial within)",
                "distinct_dlos": len(groups),
                "max_workers": worker_count,
                "dry_run_default": dry_run,
                "auto_fix_default": auto_fix,
            },
            "results": ordered_results,
        }
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in mappings: {e}"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger.info("Starting MCP server")
    mcp.run()
