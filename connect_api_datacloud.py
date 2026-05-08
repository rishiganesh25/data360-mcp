"""
Data Cloud Connect API utilities for managing data streams, mappings, and more.
Uses the Salesforce Connect REST API for Data Cloud operations.
"""

import json
import logging
from typing import Dict, List, Optional, Any

import requests

from oauth import OAuthSession

# Get logger for this module
logger = logging.getLogger(__name__)


def _handle_error_response(response: requests.Response):
    """Handle error responses from the API"""
    if response.status_code >= 300:
        message = response.text
        try:
            payload = response.json()
            if isinstance(payload, list) and len(payload) > 0:
                message = payload[0].get("message", message)
            elif isinstance(payload, dict):
                message = payload.get("message", payload.get("error", message))
        except Exception:
            pass
        raise Exception(f"API Error {response.status_code}: {message}")


def get_data_streams(oauth_session: OAuthSession) -> List[Dict[str, Any]]:
    """
    Get all data streams with their status information.
    
    Returns a list of data streams with details like:
    - name
    - status (Active, Inactive, Processing, etc.)
    - sourceObject
    - category
    - lastRefreshDate
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{base_url}/services/data/v63.0/ssot/data-streams"
    
    logger.info(f"Fetching data streams from {url}")
    response = requests.get(url, headers=headers, timeout=60)
    
    logger.info(f"Data streams response: status={response.status_code}")
    _handle_error_response(response)
    
    return response.json()


def get_data_stream_details(oauth_session: OAuthSession, data_stream_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific data stream.
    
    Args:
        data_stream_name: The API name of the data stream
        
    Returns:
        Detailed information about the data stream including mappings
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{base_url}/services/data/v63.0/ssot/data-streams/{data_stream_name}"
    
    logger.info(f"Fetching data stream details for {data_stream_name}")
    response = requests.get(url, headers=headers, timeout=60)
    
    _handle_error_response(response)
    
    return response.json()


def get_data_model_objects(oauth_session: OAuthSession) -> List[Dict[str, Any]]:
    """
    Get all Data Model Objects (DMOs) in the org.
    
    Returns a list of DMOs with their metadata.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{base_url}/services/data/v63.0/ssot/data-model-objects"
    
    logger.info(f"Fetching data model objects from {url}")
    response = requests.get(url, headers=headers, timeout=60)
    
    _handle_error_response(response)
    
    return response.json()


def get_data_model_object_details(oauth_session: OAuthSession, dmo_name: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific Data Model Object.
    
    Args:
        dmo_name: The API name of the DMO (e.g., 'ssot__Individual__dlm')
        
    Returns:
        Detailed information about the DMO including fields and relationships
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{base_url}/services/data/v63.0/ssot/data-model-objects/{dmo_name}"
    
    logger.info(f"Fetching DMO details for {dmo_name}")
    response = requests.get(url, headers=headers, timeout=60)
    
    _handle_error_response(response)
    
    return response.json()


def get_data_stream_mappings(oauth_session: OAuthSession) -> List[Dict[str, Any]]:
    """
    Get all data stream to DMO mappings.
    
    Returns a list of mappings showing how data streams map to Data Model Objects.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{base_url}/services/data/v63.0/ssot/data-model-mappings"
    
    logger.info(f"Fetching data model mappings from {url}")
    response = requests.get(url, headers=headers, timeout=60)
    
    _handle_error_response(response)
    
    return response.json()


def get_identity_resolution_rulesets(oauth_session: OAuthSession) -> List[Dict[str, Any]]:
    """
    Get all identity resolution rulesets.
    
    Returns a list of rulesets used for matching and reconciling profiles.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{base_url}/services/data/v63.0/ssot/identity-resolution/rulesets"
    
    logger.info(f"Fetching identity resolution rulesets from {url}")
    response = requests.get(url, headers=headers, timeout=60)
    
    _handle_error_response(response)
    
    return response.json()


def get_calculated_insights(oauth_session: OAuthSession) -> List[Dict[str, Any]]:
    """
    Get all calculated insights.
    
    Returns a list of calculated insights defined in Data Cloud.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{base_url}/services/data/v63.0/ssot/calculated-insights"
    
    logger.info(f"Fetching calculated insights from {url}")
    response = requests.get(url, headers=headers, timeout=60)
    
    _handle_error_response(response)
    
    return response.json()


def create_calculated_insight(
    oauth_session: OAuthSession,
    api_name: str,
    display_name: str,
    expression: str,
    description: str = "",
    data_space: str = "default",
    publish_schedule_interval: str = "TWENTY_FOUR",
    publish_schedule_start: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a Calculated Insight in Data Cloud via the Connect API.

    Dimensions and measures are derived by the server from the SQL expression's
    SELECT list — do NOT pass them in the payload.

    Args:
        api_name: Developer name, must end in '__cio' (e.g., 'customer_ltv__cio')
        display_name: Human-readable label
        expression: SELECT SQL. Reference DMO fields as <DMO>.<field> and alias every
            projected column (these become the CI dimensions/measures).
        description: Optional description
        data_space: Dataspace (default: 'default')
        publish_schedule_interval: Refresh interval enum. Known values include 'Six',
            'TWENTY_FOUR'. Defaults to daily refresh ('TWENTY_FOUR').
        publish_schedule_start: ISO datetime (e.g., '2026-05-05T02:00'). Defaults to
            now + 1 day if omitted.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"{base_url}/services/data/v63.0/ssot/calculated-insights"

    if not publish_schedule_start:
        from datetime import datetime, timedelta, timezone
        publish_schedule_start = (
            datetime.now(timezone.utc) + timedelta(days=1)
        ).strftime("%Y-%m-%dT%H:%M")

    payload = {
        "apiName": api_name,
        "displayName": display_name,
        "definitionType": "CALCULATED_METRIC",
        "dataSpaceName": data_space,
        "description": description,
        "expression": expression,
        "publishScheduleInterval": publish_schedule_interval,
        "publishScheduleStartDateTime": publish_schedule_start,
    }

    logger.info(f"Creating Calculated Insight '{api_name}' at {url}")
    response = requests.post(url, json=payload, headers=headers, timeout=120)

    if response.status_code >= 300:
        return {
            "error_status": response.status_code,
            "error_body": response.text,
            "sent_payload": payload,
        }

    try:
        body = response.json()
    except Exception:
        body = {"status": "created"}

    return {"status": "created", "apiName": api_name, "response": body}


def get_segments(oauth_session: OAuthSession) -> List[Dict[str, Any]]:
    """
    Get all segments.
    
    Returns a list of segments defined in Data Cloud.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{base_url}/services/data/v63.0/ssot/segments"
    
    logger.info(f"Fetching segments from {url}")
    response = requests.get(url, headers=headers, timeout=60)
    
    _handle_error_response(response)
    
    return response.json()


def create_segment(oauth_session: OAuthSession, segment_definition: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new segment in Data Cloud via the Connect API.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"{base_url}/services/data/v63.0/ssot/segments"

    logger.info(f"Creating segment via Connect API: {json.dumps(segment_definition)}")
    response = requests.post(url, json=segment_definition, headers=headers, timeout=120)

    if response.status_code >= 300:
        return {
            "error_status": response.status_code,
            "error_body": response.text,
            "sent_payload": segment_definition
        }

    if response.status_code in (201, 204):
        return {"status": "created", "segment": segment_definition}

    return response.json()


def create_segment_dbt(
    oauth_session: OAuthSession,
    display_name: str,
    sql: str,
    description: str = "",
    lookback_period: str = "P90D",
) -> Dict[str, Any]:
    """
    Create a DBT (SQL-based) segment in Data Cloud.
    Tries multiple API formats to find the correct one.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"{base_url}/services/data/v63.0/ssot/segments"

    payload = {
        "segmentType": "Dbt",
        "displayName": display_name,
        "description": description,
        "lookbackPeriod": lookback_period,
    }

    possible_sql_keys = [
        "sql", "sqlExpression", "sqlStatement", "segmentSql",
        "dbtSql", "queryExpression", "segmentQuery"
    ]

    results = []
    for key in possible_sql_keys:
        test_payload = {**payload, key: sql}
        logger.info(f"Trying segment creation with sql key='{key}'")
        response = requests.post(url, json=test_payload, headers=headers, timeout=120)

        body = response.text
        if response.status_code < 300:
            return {"status": "created", "sql_key": key, "response": response.json()}

        if "Unrecognized field" not in body:
            results.append({
                "sql_key": key,
                "status": response.status_code,
                "response": body
            })

    if results:
        return {"status": "found_valid_keys", "results": results}

    return {"status": "all_keys_rejected", "message": "No valid sql field name found"}


def describe_sobject(oauth_session: OAuthSession, sobject_name: str) -> Dict[str, Any]:
    """
    Describe a Salesforce sObject to get its field metadata.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"{base_url}/services/data/v63.0/sobjects/{sobject_name}/describe"

    logger.info(f"Describing sObject '{sobject_name}'")
    response = requests.get(url, headers=headers, timeout=60)

    _handle_error_response(response)

    return response.json()


def create_sobject_record(oauth_session: OAuthSession, sobject_name: str, record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a record via the Salesforce sObject REST API.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"{base_url}/services/data/v63.0/sobjects/{sobject_name}"

    logger.info(f"Creating {sobject_name} record")
    response = requests.post(url, json=record, headers=headers, timeout=120)

    _handle_error_response(response)

    return response.json()


def get_data_graphs(oauth_session: OAuthSession) -> List[Dict[str, Any]]:
    """
    Get all data graphs.
    
    Returns a list of data graphs defined in Data Cloud.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{base_url}/services/data/v63.0/ssot/data-graphs/metadata"

    logger.info(f"Fetching data graphs from {url}")
    response = requests.get(url, headers=headers, timeout=60)

    _handle_error_response(response)

    return response.json()


def _build_source_object(
    dmo: str,
    projected_fields: List[str],
    related: Optional[List[Dict[str, Any]]],
    dataspace: str,
    label: Optional[str] = None,
    parent_field: Optional[str] = None,
    child_field: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a sourceObject node (recursively) for the data graph payload."""
    fields_payload: List[Dict[str, Any]] = []
    for fname in projected_fields:
        is_kq = fname.startswith("KQ_")
        fields_payload.append({
            "dataType": "STRING",
            "isKeyColumn": fname == "ssot__Id__c",
            "isProjected": True,
            "keyQualifierName": "KQ_Id__c" if fname == "ssot__Id__c" else "",
            "sourceFieldName": fname,
            "usageTag": "KEY_QUALIFIER" if is_kq else "NONE",
        })

    path: List[Dict[str, Any]] = []
    if parent_field and child_field:
        path.append({"fieldName": child_field, "parentFieldName": parent_field})

    related_payload: List[Dict[str, Any]] = []
    for rel in (related or []):
        related_payload.append(_build_source_object(
            dmo=rel["dmo"],
            projected_fields=rel["projected_fields"],
            related=rel.get("related_objects", []),
            dataspace=dataspace,
            label=rel.get("label"),
            parent_field=rel["parent_field"],
            child_field=rel["child_field"],
        ))

    return {
        "dataspaceName": dataspace,
        "description": "",
        "label": label or dmo,
        "name": dmo,
        "fields": fields_payload,
        "path": path,
        "recencyCriteria": [],
        "relatedObjects": related_payload,
        "type": "Standard",
    }


def create_data_graph(
    oauth_session: OAuthSession,
    developer_name: str,
    primary_dmo: str,
    projected_fields: List[str],
    related_objects: Optional[List[Dict[str, Any]]] = None,
    dataspace: str = "default",
    description: str = "",
    label: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a Data Cloud data graph."""
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    source_object = _build_source_object(
        dmo=primary_dmo,
        projected_fields=projected_fields,
        related=related_objects,
        dataspace=dataspace,
        label=label or developer_name,
    )

    payload = {
        "dataspaceName": dataspace,
        "description": description,
        "label": label or developer_name,
        "name": developer_name,
        "primaryObjectName": primary_dmo,
        "sourceObject": source_object,
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-graphs"
    logger.info(f"Creating data graph {developer_name} at {url}")
    logger.debug(f"Payload: {json.dumps(payload)}")
    response = requests.post(url, json=payload, headers=headers, timeout=120)
    _handle_error_response(response)
    return response.json()


def delete_data_graph(oauth_session: OAuthSession, developer_name: str) -> Dict[str, Any]:
    """Delete a Data Cloud data graph by developer name."""
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{base_url}/services/data/v63.0/ssot/data-graphs/{developer_name}"
    logger.info(f"Deleting data graph {developer_name} at {url}")
    response = requests.delete(url, headers=headers, timeout=60)
    _handle_error_response(response)
    if response.text:
        try:
            return response.json()
        except Exception:
            pass
    return {"status": "deleted", "developerName": developer_name}


def list_connectors(oauth_session: OAuthSession) -> List[Dict[str, Any]]:
    """
    List all configured data source connectors in the org.

    Returns:
        List of connector objects with name, type, and status.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-connectors"

    logger.info("Fetching data connectors")
    response = requests.get(url, headers=headers, timeout=60)

    _handle_error_response(response)

    return response.json()


def get_connector_source_objects(
    oauth_session: OAuthSession,
    connector_name: str,
) -> List[Dict[str, Any]]:
    """
    List available source objects for a specific connector.

    Args:
        connector_name: The API name of the connector (e.g., 'SalesforceDotCom_Home')

    Returns:
        List of source objects available in this connector.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-connectors/{connector_name}/source-objects"

    logger.info(f"Fetching source objects for connector '{connector_name}'")
    response = requests.get(url, headers=headers, timeout=60)

    _handle_error_response(response)

    return response.json()


def _build_connector_payload(
    connector_type: str,
    connector_name: Optional[str] = None,
    source_object: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build the connectorInfo payload section based on connector type.

    Different connector types require different payload shapes:
    - SalesforceDotCom: connectorDetails with name + sourceObject
    - External connectors (S3, GCS, Azure, SFTP): connectorDetails with name + sourceObject
    - IngestApi: no connectorDetails needed
    """
    connector_info: Dict[str, Any] = {"connectorType": connector_type}

    if connector_type == "IngestApi":
        return connector_info

    if not connector_name:
        raise ValueError(
            f"connector_name is required for connector type '{connector_type}'"
        )
    if not source_object:
        raise ValueError(
            f"source_object is required for connector type '{connector_type}'"
        )

    connector_info["connectorDetails"] = {
        "name": connector_name,
        "sourceObject": source_object,
    }

    return connector_info


def create_data_stream(
    oauth_session: OAuthSession,
    name: str,
    connector_type: str,
    connector_name: Optional[str] = None,
    source_object: Optional[str] = None,
    category: str = "Profile",
    data_space: str = "default",
    refresh_mode: str = "UPSERT",
    extra_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a new data stream in Data Cloud for any supported connector type.

    Supported connector types include:
    - SalesforceDotCom: Standard CRM connector
    - AmazonS3: Amazon S3 bucket connector
    - GoogleCloudStorage: GCS connector
    - AzureBlobStorage: Azure Blob connector
    - Sftp: SFTP connector
    - IngestApi: Ingestion API (schema-only, data pushed via Ingestion API)
    - MuleSoft: MuleSoft connector
    - Any other connector configured in your org

    Args:
        name: The name for the data stream
        connector_type: The type of connector (e.g., 'SalesforceDotCom', 'AmazonS3', 'IngestApi')
        connector_name: The connector instance name (required for all types except IngestApi)
        source_object: The source object/file/path (required for all types except IngestApi)
        category: Object category - 'Profile', 'Engagement', or 'Other'
        data_space: The data space name
        refresh_mode: 'UPSERT' or 'OVERWRITE'
        extra_config: Optional dict merged into the top-level payload for connector-specific
                      settings (e.g., file format, delimiter, schema overrides)

    Returns:
        The created data stream details from the API response
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    connector_info = _build_connector_payload(connector_type, connector_name, source_object)

    payload: Dict[str, Any] = {
        "name": name,
        "connectorInfo": connector_info,
        "dataLakeObjectInfo": {
            "category": category,
            "dataspaceInfo": [{"name": data_space}]
        },
        "refreshConfig": {
            "refreshMode": refresh_mode
        }
    }

    if extra_config:
        for key, value in extra_config.items():
            if key in payload and isinstance(payload[key], dict) and isinstance(value, dict):
                payload[key].update(value)
            else:
                payload[key] = value

    url = f"{base_url}/services/data/v63.0/ssot/data-streams"

    logger.info(
        f"Creating data stream '{name}' (type={connector_type}, "
        f"connector={connector_name}, source={source_object})"
    )
    response = requests.post(url, json=payload, headers=headers, timeout=120)

    _handle_error_response(response)

    return response.json()


def create_ingestion_api_schema(
    oauth_session: OAuthSession,
    object_name: str,
    fields: List[Dict[str, str]],
    primary_key: str = "Id",
) -> Dict[str, Any]:
    """
    Create or update the schema for an Ingestion API data stream object.

    This is the first step for Ingestion API connectors: define the schema,
    then push data via the Bulk or Streaming Ingestion API.

    Args:
        object_name: The DLO object name for the ingestion target
        fields: List of field definitions, each with 'name' and 'type'
                (e.g., [{"name": "Id", "type": "TEXT"}, {"name": "Amount", "type": "NUMBER"}])
        primary_key: The primary key field name (default: 'Id')

    Returns:
        The schema creation response
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    field_defs = []
    for f in fields:
        field_def = {
            "name": f["name"],
            "type": f.get("type", "TEXT"),
            "isPrimaryKey": f["name"] == primary_key,
        }
        if "length" in f:
            field_def["length"] = f["length"]
        field_defs.append(field_def)

    payload = {
        "object": object_name,
        "fields": field_defs,
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-ingestion/schema"

    logger.info(f"Creating ingestion API schema for '{object_name}' with {len(fields)} fields")
    response = requests.put(url, json=payload, headers=headers, timeout=120)

    _handle_error_response(response)

    if response.status_code == 204:
        return {"status": "schema_created", "object": object_name, "fields": len(fields)}

    return response.json()


def delete_data_stream(
    oauth_session: OAuthSession,
    data_stream_name: str,
    delete_data_lake_object: bool = True,
) -> Dict[str, Any]:
    """
    Delete a data stream from Data Cloud.

    Args:
        data_stream_name: The API name of the data stream to delete
        delete_data_lake_object: Whether to also delete the underlying Data Lake Object
                                 (default: True)

    Returns:
        Status of the delete operation
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    should_delete = str(delete_data_lake_object).lower()
    url = (
        f"{base_url}/services/data/v63.0/ssot/data-streams/{data_stream_name}"
        f"?shouldDeleteDataLakeObject={should_delete}"
    )

    logger.info(f"Deleting data stream '{data_stream_name}' (deleteDataLakeObject={should_delete})")
    response = requests.delete(url, headers=headers, timeout=120)

    _handle_error_response(response)

    # DELETE often returns 204 No Content on success
    if response.status_code == 204:
        return {"status": "deleted", "dataStream": data_stream_name}

    return response.json()


def list_connector_source_objects(
    oauth_session: OAuthSession,
    connector_name: str = "SalesforceDotCom_Home",
) -> List[str]:
    """
    List the available source objects for a given connector by inspecting existing
    data streams. This helps users know which objects they can create streams from.

    Note: This is a convenience function that derives available objects from the
    existing data streams API since there is no dedicated connector-objects endpoint.

    Args:
        connector_name: The connector name to filter by (default: 'SalesforceDotCom_Home')

    Returns:
        List of source object names already in use for this connector
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-streams"

    logger.info(f"Listing source objects for connector '{connector_name}'")
    response = requests.get(url, headers=headers, timeout=60)

    _handle_error_response(response)

    result = response.json()
    streams = result.get("dataStreams", result) if isinstance(result, dict) else result

    source_objects = []
    for stream in streams:
        connector_info = stream.get("connectorInfo", {})
        details = connector_info.get("connectorDetails", {})
        if details.get("name") == connector_name:
            obj = details.get("sourceObject")
            if obj:
                source_objects.append(obj)

    return sorted(source_objects)


def refresh_data_stream(oauth_session: OAuthSession, data_stream_name: str) -> Dict[str, Any]:
    """
    Trigger a refresh for a specific data stream.
    
    Args:
        data_stream_name: The API name of the data stream to refresh
        
    Returns:
        Response indicating the refresh was triggered
    
    Note: This may not work for all data stream types (e.g., Salesforce CRM connectors).
    For SFDC data streams, use the Data Cloud Setup UI to trigger refreshes.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Try the ingestion API endpoint first
    url = f"{base_url}/services/data/v63.0/ssot/data-ingestion/jobs"
    
    payload = {
        "object": data_stream_name,
        "operation": "upsert"
    }
    
    logger.info(f"Triggering refresh for data stream {data_stream_name}")
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    
    # If ingestion API fails, try the direct refresh endpoint
    if response.status_code >= 400:
        url = f"{base_url}/services/data/v63.0/ssot/data-streams/{data_stream_name}/actions/refresh"
        response = requests.post(url, headers=headers, timeout=60)
    
    if response.status_code >= 400:
        return {
            "error": "Refresh not supported via API for this data stream type",
            "dataStream": data_stream_name,
            "suggestion": "For Salesforce CRM data streams, please use the Data Cloud Setup UI to trigger a refresh: Setup → Data Cloud → Data Streams → Contact_Home → Refresh"
        }

    return {"status": "Refresh triggered", "dataStream": data_stream_name}


def get_retrievers(oauth_session: OAuthSession) -> Dict[str, Any]:
    """
    List Data Cloud retrievers via the machine-learning API.
    Uses v61.0 because that is the version where this endpoint is available.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    url = f"{base_url}/services/data/v61.0/ssot/machine-learning/retrievers"
    response = requests.get(url, headers=headers, timeout=60)
    _handle_error_response(response)
    return response.json()


def get_search_indexes(oauth_session: OAuthSession) -> Dict[str, Any]:
    """
    List Data Cloud search indexes (semantic search definitions).
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    url = f"{base_url}/services/data/v63.0/ssot/search-index"
    response = requests.get(url, headers=headers, timeout=60)
    _handle_error_response(response)
    return response.json()
