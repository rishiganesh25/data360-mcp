import json
import logging
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
    sql = f"SELECT a.attname FROM pg_catalog.pg_namespace n JOIN pg_catalog.pg_class c ON (c.relnamespace = n.oid) JOIN pg_catalog.pg_attribute a ON (a.attrelid = c.oid) JOIN pg_catalog.pg_type t ON (a.atttypid = t.oid) LEFT JOIN pg_catalog.pg_attrdef def ON (a.attrelid = def.adrelid AND a.attnum = def.adnum) LEFT JOIN pg_catalog.pg_description dsc ON (c.oid = dsc.objoid AND a.attnum = dsc.objsubid) LEFT JOIN pg_catalog.pg_class dc ON (dc.oid = dsc.classoid AND dc.relname = 'pg_class') LEFT JOIN pg_catalog.pg_namespace dn ON (dc.relnamespace = dn.oid AND dn.nspname = 'pg_catalog') WHERE a.attnum > 0 AND NOT a.attisdropped AND c.relname='{table}'"
    result = run_query(oauth_session, sql)
    # Extract data from the result dictionary
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
        default="TWENTY_FOUR",
        description="Refresh interval enum. Known values: 'Six' (6-hour), 'TWENTY_FOUR' (daily). Default: daily."),
    publish_schedule_start: str = Field(
        default="",
        description="Optional ISO datetime for first run (e.g., '2026-05-05T02:00'). Defaults to now + 1 day."),
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


@mcp.tool(description="Makes a generic Salesforce REST API call. Useful for exploring APIs.")
def sf_rest_api(
    method: str = Field(description="HTTP method: GET, POST, PATCH, DELETE"),
    path: str = Field(description="API path starting with / (e.g., /services/data/v63.0/sobjects/MarketSegment)"),
    body: str = Field(default="", description="Optional JSON request body for POST/PATCH"),
) -> dict:
    """Execute an arbitrary Salesforce REST API call."""
    try:
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
        return {"error": str(e)}


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


@mcp.tool(description="Deletes a Data Cloud data graph by developer name")
def delete_data_graph(
    developer_name: str = Field(description="Developer name of the data graph to delete"),
) -> dict:
    try:
        return _delete_data_graph(oauth_session, developer_name)
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
    "Creates a new data stream in Data Cloud from any supported connector type. "
    "Supported connectors include: SalesforceDotCom, AmazonS3, GoogleCloudStorage, "
    "AzureBlobStorage, Sftp, MuleSoft, IngestApi, and any other connector configured in your org. "
    "Use 'list_connectors' first to discover available connectors and their names."
))
def create_new_data_stream(
    stream_name: str = Field(
        description="The name for the data stream (e.g., 'Lead_Home', 'Orders_S3', 'CustomerEvents')"),
    connector_type: str = Field(
        description=(
            "The connector type. Common values: "
            "'SalesforceDotCom' (CRM), 'AmazonS3' (S3 bucket), "
            "'GoogleCloudStorage' (GCS), 'AzureBlobStorage' (Azure), "
            "'Sftp' (SFTP server), 'MuleSoft', 'IngestApi' (push via Ingestion API)"
        )),
    connector_name: str = Field(
        default="",
        description=(
            "The connector instance name as shown by list_connectors "
            "(e.g., 'SalesforceDotCom_Home', 'My_S3_Connector'). "
            "Required for all types except 'IngestApi'."
        )),
    source_object: str = Field(
        default="",
        description=(
            "The source object, file path, or bucket path to ingest. "
            "For SalesforceDotCom: the object API name (e.g., 'Lead', 'Opportunity'). "
            "For AmazonS3/GCS/Azure: the file or prefix path. "
            "Not required for 'IngestApi'."
        )),
    category: str = Field(
        default="Profile",
        description="The object category: 'Profile' (people/accounts), 'Engagement' (events/interactions), or 'Other'"),
    data_space: str = Field(
        default="default",
        description="The data space to deploy to"),
    refresh_mode: str = Field(
        default="UPSERT",
        description="The refresh mode: 'UPSERT' (incremental) or 'OVERWRITE' (full replace)"),
    extra_config: str = Field(
        default="",
        description=(
            "Optional JSON string with extra connector-specific configuration merged into the payload. "
            "For example, file format settings: "
            '{\"dataLakeObjectInfo\": {\"fileFormat\": \"CSV\", \"delimiter\": \",\"}}. '
            "Leave empty if not needed."
        )),
) -> dict:
    """
    Create a new data stream to ingest data from any supported connector into Data Cloud.
    Use list_connectors to discover available connectors before calling this.
    """
    try:
        parsed_extra = None
        if extra_config and extra_config.strip():
            parsed_extra = json.loads(extra_config)

        result = create_data_stream(
            oauth_session,
            name=stream_name,
            connector_type=connector_type,
            connector_name=connector_name or None,
            source_object=source_object or None,
            category=category,
            data_space=data_space,
            refresh_mode=refresh_mode,
            extra_config=parsed_extra,
        )
        return {
            "status": "created",
            "dataStream": stream_name,
            "connectorType": connector_type,
            "connector": connector_name,
            "sourceObject": source_object,
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


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger.info("Starting MCP server")
    mcp.run()
