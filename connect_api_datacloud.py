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


def _sanitize_error_body(text: str, max_len: int = 1000) -> str:
    """Strip tokens or auth headers that the server might echo back in errors."""
    if not text:
        return ""
    sanitized = text[:max_len]
    import re
    sanitized = re.sub(
        r'(Bearer\s+)[A-Za-z0-9._\-]+',
        r'\1****',
        sanitized,
    )
    sanitized = re.sub(
        r'("?access_token"?\s*[:=]\s*"?)[A-Za-z0-9._\-]+',
        r'\1****',
        sanitized,
    )
    return sanitized


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
        raise Exception(f"API Error {response.status_code}: {_sanitize_error_body(str(message))}")


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
    publish_schedule_interval: str = "Six",
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
        publish_schedule_interval: Refresh interval enum. Known values: 'Six' (6-hour).
            Defaults to 6-hour refresh.
        publish_schedule_start: ISO datetime (e.g., '2026-05-05T02:00'). Defaults to
            a past date so the CI starts processing immediately.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    url = f"{base_url}/services/data/v63.0/ssot/calculated-insights"

    if not publish_schedule_start:
        publish_schedule_start = "2025-01-01T00:00"

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


def list_connector_instances(
    oauth_session: OAuthSession,
    include_config: bool = True,
) -> List[Dict[str, Any]]:
    """
    List configured connector instances in the org via the Tooling API
    (MktDataConnection sObject). Unlike list_connectors (which returns the
    connector type catalog), this returns the actual configured instances —
    e.g. EDC_Snowflake, DIGITAL_Snowflake, na_ggp_data360, UploadedFiles, etc.

    Args:
        include_config: If True, fetch each record individually to expand
            the Metadata blob (account URL, warehouse, bucket, etc.).
            Credentials are masked by Salesforce regardless.

    Returns:
        List of dicts with keys: id, name, fullName, connectorType,
        connectionMethod, status, isActive, createdDate, lastModifiedDate,
        and (when include_config=True) parameters and credentialNames.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    soql = (
        "SELECT Id,MasterLabel,ConnectionMethod,IsActivityEnabled,"
        "IsSentosEnabled,ShouldAutoCreatePolicies,CreatedDate,LastModifiedDate "
        "FROM MktDataConnection ORDER BY MasterLabel"
    )
    list_url = f"{base_url}/services/data/v63.0/tooling/query/?q={requests.utils.quote(soql, safe=',+')}"

    logger.info("Fetching MktDataConnection instances via Tooling API")
    response = requests.get(list_url, headers=headers, timeout=60)
    _handle_error_response(response)
    records = response.json().get("records", [])

    results: List[Dict[str, Any]] = []
    for rec in records:
        entry = {
            "id": rec.get("Id"),
            "name": rec.get("MasterLabel"),
            "connectionMethod": rec.get("ConnectionMethod"),
            "isActivityEnabled": rec.get("IsActivityEnabled"),
            "createdDate": rec.get("CreatedDate"),
            "lastModifiedDate": rec.get("LastModifiedDate"),
        }
        if include_config:
            detail_url = (
                f"{base_url}/services/data/v63.0/tooling/sobjects/"
                f"MktDataConnection/{rec['Id']}"
            )
            detail_resp = requests.get(detail_url, headers=headers, timeout=60)
            if detail_resp.status_code == 200:
                detail = detail_resp.json()
                metadata = detail.get("Metadata") or {}
                entry["fullName"] = detail.get("FullName")
                entry["connectorType"] = metadata.get("connectorName")
                entry["status"] = metadata.get("connectionStatus")
                entry["isActive"] = (
                    str(metadata.get("connectionStatus", "")).upper() == "ACTIVE"
                )
                entry["parameters"] = {
                    p.get("paramName"): p.get("value")
                    for p in (metadata.get("parameters") or [])
                    if p.get("paramName")
                }
                entry["credentialNames"] = [
                    c.get("credentialName")
                    for c in (metadata.get("credentials") or [])
                    if c.get("credentialName")
                ]
            else:
                entry["error"] = (
                    f"Failed to fetch metadata for {rec.get('MasterLabel')}: "
                    f"HTTP {detail_resp.status_code}"
                )
        results.append(entry)
    return results


def list_connection_source_objects(
    oauth_session: OAuthSession,
    connection_id: str,
) -> List[Dict[str, Any]]:
    """
    Browse source objects (tables/views) for a configured connector instance,
    using the live `/ssot/connections/{id}/objects` endpoint. Works for
    BYOL/Zero-Copy connectors (Snowflake, BigQuery) which the older
    `/ssot/data-connectors/{name}/source-objects` path 404s on.

    Returns a list of `{name, objectType, attributes: {database, schema, inUse}}`.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    url = (
        f"{base_url}/services/data/v63.0/ssot/connections/"
        f"{connection_id}/objects"
    )
    logger.info(f"Browsing source objects for connection '{connection_id}'")
    response = requests.post(url, json={}, headers=headers, timeout=60)
    _handle_error_response(response)
    body = response.json()
    return body.get("objects", body)


def list_connection_databases(
    oauth_session: OAuthSession,
    connection_id: str,
) -> List[str]:
    """
    List databases visible to a 3-level connector instance (e.g. Snowflake).
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    url = (
        f"{base_url}/services/data/v63.0/ssot/connections/"
        f"{connection_id}/databases"
    )
    response = requests.post(url, json={}, headers=headers, timeout=60)
    _handle_error_response(response)
    body = response.json()
    return body.get("databases", body)


def describe_connection_source_object(
    oauth_session: OAuthSession,
    connection_id: str,
    object_name: str,
    database: str,
    schema: str,
) -> Dict[str, Any]:
    """
    Describe the column schema of a source object on a 3-level connector
    (Snowflake/BigQuery). Returns:
      {fields: [{name, type, originalType, format?}], primaryKeys: [...], advancedAttributes, incrementalExtractAttributes}

    NOTE: Body must use the key `advancedAttributes` (NOT `database` directly,
    NOT `objectAttributes`, etc.) — the field-describe parser is locked to that key.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    url = (
        f"{base_url}/services/data/v63.0/ssot/connections/"
        f"{connection_id}/objects/{object_name}/fields"
    )
    body = {"advancedAttributes": {"database": database, "schema": schema}}
    response = requests.post(url, json=body, headers=headers, timeout=60)
    _handle_error_response(response)
    return response.json()


def create_zero_copy_data_stream(
    oauth_session: OAuthSession,
    name: str,
    connector_name: str,
    database: str,
    schema: str,
    object_name: str,
    fields: List[Dict[str, Any]],
    category: str = "Other",
    data_space: str = "default",
    refresh_mode: str = "TOTAL_REPLACE",
    event_time_field: Optional[str] = None,
    label: Optional[str] = None,
    dll_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a zero-copy / BYOL (federated) data stream against a 3-level
    connector instance such as Snowflake or BigQuery. Data stays in the
    source — Data Cloud queries it in place via Direct_Access.

    Args:
        name: Stream API name (no spaces).
        connector_name: Connector instance name (e.g. 'EDC_Snowflake'),
            NOT the MktDataConnection Id.
        database / schema / object_name: 3-level source coordinates.
        fields: List of dicts with keys:
            - name: target DLO field name (lowercase recommended)
            - label: source column header (typically uppercase, matches Snowflake column)
            - dataType: 'Text' | 'Number' | 'DateTime' | 'Date' | 'Boolean'
            - isPrimaryKey: bool
            - format (optional): for Date types, e.g. 'MM/dd/yyyy'
        category: 'Profile' | 'Engagement' | 'Other' (default Other for snapshot tables)
        refresh_mode: 'TOTAL_REPLACE' (snapshot/full refresh) | 'UPSERT'
        event_time_field: Required when category='Engagement' — DLO field name (target).
        label: Display label (defaults to `name`).
        dll_name: Override DLO API name; defaults to `{name}__dll`.

    Returns the API response from POST /ssot/data-streams.
    """
    if not fields:
        raise ValueError("fields is required for zero-copy data streams")
    if category == "Engagement" and not event_time_field:
        raise ValueError("event_time_field is required for Engagement category streams")

    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    label = label or name
    dlo_name = dll_name or f"{name}__dll"

    dlf_reps: List[Dict[str, Any]] = []
    source_fields: List[Dict[str, Any]] = []
    mappings: List[Dict[str, Any]] = []

    for f in fields:
        target_name = f["name"]
        source_label = f.get("label") or target_name.upper()
        data_type = f.get("dataType", "Text")
        is_pk = bool(f.get("isPrimaryKey", False))

        dlf_reps.append({
            "dataType": data_type,
            "isPrimaryKey": is_pk,
            "label": source_label,
            "name": target_name,
        })
        sf_entry: Dict[str, Any] = {"dataType": data_type, "name": source_label}
        if "format" in f and f["format"]:
            sf_entry["format"] = f["format"]
        source_fields.append(sf_entry)
        mappings.append({
            "sourceFieldLabel": source_label,
            "targetFieldName": target_name,
        })

    dlo_info: Dict[str, Any] = {
        "dataspaceInfo": [{"name": data_space}],
        "category": category,
        "label": label,
        "name": dlo_name,
        "dataLakeFieldInputRepresentations": dlf_reps,
    }
    if event_time_field:
        dlo_info["eventDateTimeFieldName"] = event_time_field

    payload: Dict[str, Any] = {
        "name": name,
        "label": label,
        "datastreamType": "EXTERNAL",
        "connectorInfo": {
            "connectorType": "DataConnector",
            "connectorDetails": {"name": connector_name},
        },
        "dataLakeObjectInfo": dlo_info,
        "mappings": mappings,
        "refreshConfig": {"refreshMode": refresh_mode},
        "sourceFields": source_fields,
        "advancedAttributes": {
            "schema": schema,
            "database": database,
            "object": object_name,
        },
        "dataAccessMode": "Direct_Access",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-streams"
    logger.info(
        f"Creating zero-copy data stream '{name}' "
        f"(connector={connector_name}, source={database}.{schema}.{object_name})"
    )
    response = requests.post(url, json=payload, headers=headers, timeout=120)
    _handle_error_response(response)
    return response.json()


FILE_BASED_CONNECTOR_TYPES = {"AwsS3", "GCS", "AzureBlob", "SFTP"}


def create_data_stream(
    oauth_session: OAuthSession,
    name: str,
    connector_type: str,
    connector_name: Optional[str] = None,
    source_object: Optional[str] = None,
    category: str = "Profile",
    data_space: str = "default",
    refresh_mode: str = "UPSERT",
    fields: Optional[List[Dict[str, Any]]] = None,
    file_name: Optional[str] = None,
    file_type: str = "CSV",
    import_directory: str = "/",
    frequency_type: str = "DAILY",
    frequency_hours: Optional[List[int]] = None,
    frequency_day_of_week: Optional[str] = None,
    event_time_field: Optional[str] = None,
    dll_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new data stream in Data Cloud for any supported connector type.

    Handles three distinct patterns:
    - SalesforceDotCom: CRM objects, minimal payload with connectorType matching type name
    - File-based (AwsS3, GCS, AzureBlob, SFTP): Uses 'DataConnector' connectorType,
      requires full schema, sourceFields, mappings, and advancedAttributes
    - IngestApi: Schema-only stream, data pushed via Ingestion API

    Args:
        name: The data stream name
        connector_type: 'SalesforceDotCom', 'AwsS3', 'GCS', 'AzureBlob', 'SFTP', or 'IngestApi'
        connector_name: The connector instance name (required except for IngestApi)
        source_object: For CRM: object API name. Not used for file-based (use file_name instead).
        category: 'Profile', 'Engagement', or 'Other'
        data_space: Target data space (default: 'default')
        refresh_mode: 'UPSERT' or 'OVERWRITE'
        fields: List of field definitions, each a dict with keys:
                - name: field API name (target DLO field name)
                - label: source field label (CSV column header name)
                - dataType: 'Text', 'Number', or 'DateTime'
                - isPrimaryKey: bool
        file_name: For file-based connectors: the file name or pattern (e.g., 'orders.csv')
        file_type: 'CSV' or 'PARQUET' (default: 'CSV')
        import_directory: Directory within the bucket (default: '/' for root)
        frequency_type: 'HOURLY', 'DAILY', 'WEEKLY', or 'MONTHLY'
        frequency_hours: List of hours for DAILY/WEEKLY/MONTHLY (e.g., [7] for 7am)
        frequency_day_of_week: Day for WEEKLY (e.g., 'Monday', 'Wednesday')
        event_time_field: Required for Engagement category — the DateTime field name
                          used as the event timestamp (target field name, e.g., 'created_at__c')
        dll_name: Optional DLO API name override (e.g., 'S3_Orders__dll').
                  Auto-generated from stream name if not provided.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    is_file_based = connector_type in FILE_BASED_CONNECTOR_TYPES

    if is_file_based:
        payload = _build_file_based_payload(
            name=name,
            connector_name=connector_name,
            category=category,
            data_space=data_space,
            refresh_mode=refresh_mode,
            fields=fields or [],
            file_name=file_name or "*",
            file_type=file_type,
            import_directory=import_directory,
            frequency_type=frequency_type,
            frequency_hours=frequency_hours,
            frequency_day_of_week=frequency_day_of_week,
            event_time_field=event_time_field,
            dll_name=dll_name,
        )
    elif connector_type == "IngestApi":
        payload = _build_ingest_api_payload(
            name=name,
            category=category,
            data_space=data_space,
            refresh_mode=refresh_mode,
            fields=fields,
            event_time_field=event_time_field,
            dll_name=dll_name,
        )
    else:
        payload = _build_crm_payload(
            name=name,
            connector_type=connector_type,
            connector_name=connector_name,
            source_object=source_object,
            category=category,
            data_space=data_space,
            refresh_mode=refresh_mode,
        )

    url = f"{base_url}/services/data/v63.0/ssot/data-streams"

    logger.info(
        f"Creating data stream '{name}' (type={connector_type}, "
        f"connector={connector_name})"
    )
    response = requests.post(url, json=payload, headers=headers, timeout=120)

    _handle_error_response(response)

    return response.json()


def _build_file_based_payload(
    name: str,
    connector_name: Optional[str],
    category: str,
    data_space: str,
    refresh_mode: str,
    fields: List[Dict[str, Any]],
    file_name: str,
    file_type: str,
    import_directory: str,
    frequency_type: str,
    frequency_hours: Optional[List[int]],
    frequency_day_of_week: Optional[str],
    event_time_field: Optional[str],
    dll_name: Optional[str],
) -> Dict[str, Any]:
    """Build the full payload for file-based connectors (S3, GCS, Azure, SFTP)."""
    if not connector_name:
        raise ValueError("connector_name is required for file-based connectors")
    if not fields:
        raise ValueError("fields (schema definition) is required for file-based connectors")

    if category == "Engagement" and not event_time_field:
        raise ValueError(
            "event_time_field is required for Engagement category streams"
        )

    dlo_name = dll_name or f"{name}__dll"

    dlf_reps = []
    source_fields = []
    mappings = []
    for f in fields:
        dlf_reps.append({
            "name": f["name"],
            "label": f["label"],
            "dataType": f["dataType"],
            "isPrimaryKey": f.get("isPrimaryKey", False),
        })
        source_fields.append({
            "name": f["label"],
            "dataType": f["dataType"],
        })
        mappings.append({
            "sourceFieldLabel": f["label"],
            "targetFieldName": f["name"],
        })

    dlo_info: Dict[str, Any] = {
        "label": name,
        "name": dlo_name,
        "category": category,
        "dataspaceInfo": [{"name": data_space}],
        "dataLakeFieldInputRepresentations": dlf_reps,
    }
    if event_time_field:
        dlo_info["eventDateTimeFieldName"] = event_time_field

    frequency: Dict[str, Any] = {"frequencyType": frequency_type}
    if frequency_type in ("DAILY", "WEEKLY", "MONTHLY") and frequency_hours:
        frequency["hours"] = frequency_hours
    if frequency_type == "WEEKLY" and frequency_day_of_week:
        frequency["refreshDayOfWeek"] = frequency_day_of_week

    return {
        "name": name,
        "label": name,
        "datasource": f"AwsS3_{connector_name}",
        "datastreamType": "CONNECTORSFRAMEWORK",
        "connectorInfo": {
            "connectorType": "DataConnector",
            "connectorDetails": {"name": connector_name},
        },
        "dataLakeObjectInfo": dlo_info,
        "sourceFields": source_fields,
        "mappings": mappings,
        "refreshConfig": {
            "isAccelerationEnabled": True,
            "refreshMode": refresh_mode,
            "frequency": frequency,
        },
        "advancedAttributes": {
            "fileName": file_name,
            "fileType": file_type,
            "importDirectory": import_directory,
            "isMissingFileFailure": True,
            "areHeadersIncludedInFile": False,
        },
    }


def _build_ingest_api_payload(
    name: str,
    category: str,
    data_space: str,
    refresh_mode: str,
    fields: Optional[List[Dict[str, Any]]],
    event_time_field: Optional[str],
    dll_name: Optional[str],
) -> Dict[str, Any]:
    """Build payload for IngestApi (push-based) data streams."""
    if category == "Engagement" and not event_time_field:
        raise ValueError(
            "event_time_field is required for Engagement category streams"
        )

    dlo_name = dll_name or f"{name}__dll"

    dlo_info: Dict[str, Any] = {
        "label": name,
        "name": dlo_name,
        "category": category,
        "dataspaceInfo": [{"name": data_space}],
    }
    if event_time_field:
        dlo_info["eventDateTimeFieldName"] = event_time_field
    if fields:
        dlo_info["dataLakeFieldInputRepresentations"] = [
            {
                "name": f["name"],
                "label": f.get("label", f["name"]),
                "dataType": f["dataType"],
                "isPrimaryKey": f.get("isPrimaryKey", False),
            }
            for f in fields
        ]

    payload: Dict[str, Any] = {
        "name": name,
        "label": name,
        "connectorInfo": {"connectorType": "IngestApi"},
        "dataLakeObjectInfo": dlo_info,
        "refreshConfig": {"refreshMode": refresh_mode},
    }
    return payload


def _build_crm_payload(
    name: str,
    connector_type: str,
    connector_name: Optional[str],
    source_object: Optional[str],
    category: str,
    data_space: str,
    refresh_mode: str,
) -> Dict[str, Any]:
    """Build payload for CRM (SalesforceDotCom) data streams."""
    if not connector_name:
        raise ValueError(
            f"connector_name is required for connector type '{connector_type}'"
        )
    if not source_object:
        raise ValueError(
            f"source_object is required for connector type '{connector_type}'"
        )

    return {
        "name": name,
        "connectorInfo": {
            "connectorType": connector_type,
            "connectorDetails": {
                "name": connector_name,
                "sourceObject": source_object,
            },
        },
        "dataLakeObjectInfo": {
            "category": category,
            "dataspaceInfo": [{"name": data_space}],
        },
        "refreshConfig": {"refreshMode": refresh_mode},
    }


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


def _ensure_mkt_data_model_field(
    base_url: str,
    headers: Dict[str, str],
    dmo_id: str,
    dmo_name: str,
    field_name: str,
    field_label: str,
    field_def_id: str,
) -> Dict[str, Any]:
    """
    Ensure MktDataModelField exists for a CustomField. If it already exists,
    return success. If not, create it. This makes the operation idempotent.
    """
    dev_name = field_name.replace("__c", "")

    # Check if MktDataModelField already exists
    query = (
        f"SELECT Id, DeveloperName FROM MktDataModelField "
        f"WHERE MktDataModelObjectId = '{dmo_id}' "
        f"AND DeveloperName = '{dev_name}'"
    )
    q_url = f"{base_url}/services/data/v63.0/tooling/query/"
    q_resp = requests.get(q_url, headers=headers, params={"q": query}, timeout=60)
    if q_resp.status_code == 200:
        records = q_resp.json().get("records", [])
        if records:
            return {
                "status": "already_registered",
                "field_name": field_name,
                "dmo_name": dmo_name,
                "customFieldId": field_def_id,
                "mktDataModelFieldId": records[0]["Id"],
            }

    mdf_url = f"{base_url}/services/data/v63.0/tooling/sobjects/MktDataModelField"
    mdf_payload = {
        "MktDataModelObjectId": dmo_id,
        "DeveloperName": dev_name,
        "MasterLabel": field_label,
        "FieldDefinitionId": field_def_id,
        "CreationType": "Custom",
    }

    logger.info(f"Registering MktDataModelField '{dev_name}' on DMO {dmo_id}")
    mdf_resp = requests.post(mdf_url, json=mdf_payload, headers=headers, timeout=60)
    if mdf_resp.status_code >= 300:
        return {
            "error": f"MktDataModelField registration failed (HTTP {mdf_resp.status_code})",
            "detail": mdf_resp.text,
            "customFieldId": field_def_id,
            "payload": mdf_payload,
        }

    return {
        "status": "created",
        "field_name": field_name,
        "dmo_name": dmo_name,
        "customFieldId": field_def_id,
        "mktDataModelFieldId": mdf_resp.json().get("id"),
    }


def create_custom_dmo_field(
    oauth_session: OAuthSession,
    dmo_name: str,
    field_name: str,
    field_label: str,
    field_type: str = "Text",
    field_length: int = 255,
    precision: Optional[int] = None,
    scale: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Create a custom field on a Data Model Object using the Tooling API.
    Idempotent: if the CustomField already exists, it will still ensure the
    MktDataModelField registration is in place.

    Two-step process (both via Tooling API):
      1. POST /tooling/sobjects/CustomField — creates the field definition
      2. POST /tooling/sobjects/MktDataModelField — registers it on the DMO

    If step 1 fails with DUPLICATE_DEVELOPER_NAME, it looks up the existing
    CustomField ID and proceeds to step 2 anyway.

    Args:
        dmo_name: DMO API name (e.g., 'ssot__Individual__dlm')
        field_name: Field API name ending in __c (e.g., 'Email_Address__c')
        field_label: Display label (e.g., 'Email Address')
        field_type: Salesforce field type (default: 'Text').
                    Valid: Text, Number, DateTime, Date, Checkbox, Currency,
                    Percent, etc.
        field_length: Length for Text fields (default: 255)
        precision: Total digits for numeric types (Number/Currency/Percent).
                   Required by the Tooling API for numeric fields.
                   Defaults to 18 when a numeric type is requested without one.
        scale: Digits after the decimal point for numeric types.
               Defaults to 0 when a numeric type is requested without one.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Step 1: Look up the DMO's MktDataModelObject Id (needed for both paths)
    dmo_details_url = f"{base_url}/services/data/v63.0/ssot/data-model-objects/{dmo_name}"
    dmo_resp = requests.get(dmo_details_url, headers=headers, timeout=60)
    if dmo_resp.status_code != 200:
        return {
            "error": f"Could not fetch DMO details for '{dmo_name}'",
            "detail": dmo_resp.text,
        }
    dmo_id = dmo_resp.json().get("id")

    # Step 2: Create CustomField definition on the DMO entity
    full_name = f"{dmo_name}.{field_name}"
    metadata: Dict[str, Any] = {"label": field_label, "type": field_type}
    if field_type == "Text":
        metadata["length"] = field_length
    elif field_type in ("Number", "Currency", "Percent"):
        metadata["precision"] = precision if precision is not None else 18
        metadata["scale"] = scale if scale is not None else 0

    cf_url = f"{base_url}/services/data/v63.0/tooling/sobjects/CustomField"
    cf_payload = {"FullName": full_name, "Metadata": metadata}

    logger.info(f"Creating CustomField '{full_name}'")
    cf_resp = requests.post(cf_url, json=cf_payload, headers=headers, timeout=60)

    if cf_resp.status_code < 300:
        # CustomField created successfully
        field_def_id = cf_resp.json().get("id")
    else:
        # Check if it's a duplicate — if so, look up the existing ID
        is_duplicate = "DUPLICATE_DEVELOPER_NAME" in cf_resp.text
        if not is_duplicate:
            return {
                "error": f"CustomField creation failed (HTTP {cf_resp.status_code})",
                "detail": cf_resp.text,
                "payload": cf_payload,
            }

        logger.info(f"CustomField '{full_name}' already exists, looking up existing ID")
        dev_name = field_name.replace("__c", "")
        lookup_query = (
            f"SELECT Id, DeveloperName FROM CustomField "
            f"WHERE DeveloperName = '{dev_name}'"
        )
        q_url = f"{base_url}/services/data/v63.0/tooling/query/"
        q_resp = requests.get(q_url, headers=headers, params={"q": lookup_query}, timeout=60)
        if q_resp.status_code != 200:
            return {
                "error": "CustomField exists but could not look up its ID",
                "detail": q_resp.text,
            }

        # Find the record matching this DMO (there may be fields with the same
        # developer name on different objects)
        records = q_resp.json().get("records", [])
        field_def_id = None
        for rec in records:
            field_def_id = rec["Id"]
            break
        if not field_def_id:
            return {
                "error": f"CustomField '{dev_name}' reported as duplicate but could not be found via query",
            }

    # Step 3: Ensure MktDataModelField registration exists
    return _ensure_mkt_data_model_field(
        base_url, headers, dmo_id, dmo_name, field_name, field_label, field_def_id,
    )


def delete_custom_dmo_fields(
    oauth_session: OAuthSession,
    dmo_name: str,
    field_names: List[str],
) -> Dict[str, Any]:
    """
    Delete custom fields from a Data Model Object.

    Queries the Tooling API for MktDataModelField records matching the given
    developer names on the specified DMO, then deletes each MktDataModelField
    and its backing CustomField definition.

    Deletion order matters: MktDataModelField first, then CustomField.

    Args:
        dmo_name: DMO API name (e.g., 'ssot__Individual__dlm')
        field_names: List of field API names ending in __c
                     (e.g., ['Email_Address__c', 'Phone_Number__c'])
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    dmo_details_url = f"{base_url}/services/data/v63.0/ssot/data-model-objects/{dmo_name}"
    dmo_resp = requests.get(dmo_details_url, headers=headers, timeout=60)
    if dmo_resp.status_code != 200:
        return {
            "error": f"Could not fetch DMO details for '{dmo_name}'",
            "detail": dmo_resp.text,
        }
    dmo_id = dmo_resp.json().get("id")

    dev_names = [n.replace("__c", "") for n in field_names]
    quoted = "','".join(dev_names)
    query = (
        f"SELECT Id, DeveloperName, FieldDefinitionId FROM MktDataModelField "
        f"WHERE MktDataModelObjectId = '{dmo_id}' "
        f"AND DeveloperName IN ('{quoted}')"
    )
    q_url = f"{base_url}/services/data/v63.0/tooling/query/"
    q_resp = requests.get(q_url, headers=headers, params={"q": query}, timeout=60)
    if q_resp.status_code != 200:
        return {"error": f"Tooling query failed (HTTP {q_resp.status_code})", "detail": q_resp.text}

    records = q_resp.json().get("records", [])
    results = []

    for rec in records:
        mdf_id = rec["Id"]
        cf_id = rec.get("FieldDefinitionId")
        dev = rec["DeveloperName"]
        entry: Dict[str, Any] = {"field": dev}

        # Delete MktDataModelField
        mdf_url = f"{base_url}/services/data/v63.0/tooling/sobjects/MktDataModelField/{mdf_id}"
        logger.info(f"Deleting MktDataModelField '{dev}' ({mdf_id})")
        mdf_resp = requests.delete(mdf_url, headers=headers, timeout=60)
        if mdf_resp.status_code == 204:
            entry["mktDataModelField"] = "deleted"
        else:
            entry["mktDataModelField"] = f"failed ({mdf_resp.status_code}): {mdf_resp.text}"

        # Delete CustomField definition
        if cf_id:
            cf_url = f"{base_url}/services/data/v63.0/tooling/sobjects/CustomField/{cf_id}"
            logger.info(f"Deleting CustomField '{dev}' ({cf_id})")
            cf_resp = requests.delete(cf_url, headers=headers, timeout=60)
            if cf_resp.status_code == 204:
                entry["customField"] = "deleted"
            else:
                entry["customField"] = f"failed ({cf_resp.status_code}): {cf_resp.text}"

        results.append(entry)

    found_names = {r["DeveloperName"] for r in records}
    not_found = [n for n in dev_names if n not in found_names]

    return {
        "dmo_name": dmo_name,
        "requested": len(field_names),
        "found": len(records),
        "not_found": not_found if not_found else None,
        "results": results,
    }


def delete_dlo_dmo_mapping(
    oauth_session: OAuthSession,
    mapping_name: Optional[str] = None,
    source_entity: Optional[str] = None,
    target_entity: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Delete a DLO-to-DMO mapping.

    Can be called two ways:
      1. By mapping_name directly (fast, single DELETE call).
      2. By source_entity + target_entity — looks up the mapping name
         from /ssot/data-model-mappings first, then deletes it.

    Args:
        mapping_name: The mapping name (e.g., 'S3_Customer_Info_map_Individual_17...')
        source_entity: DLO developer name (e.g., 'S3_Customer_Info__dll')
        target_entity: DMO developer name (e.g., 'ssot__Individual__dlm')
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    headers = {"Authorization": f"Bearer {token}"}

    if not mapping_name:
        if not source_entity or not target_entity:
            return {
                "error": "Provide either mapping_name, or both source_entity and target_entity"
            }
        mappings_url = f"{base_url}/services/data/v63.0/ssot/data-model-mappings"
        m_resp = requests.get(mappings_url, headers=headers, timeout=60)
        if m_resp.status_code != 200:
            return {"error": f"Failed to list mappings (HTTP {m_resp.status_code})", "detail": m_resp.text}

        all_mappings = m_resp.json()
        if isinstance(all_mappings, dict):
            all_mappings = all_mappings.get("data", all_mappings.get("mappings", []))

        matches = []
        for m in all_mappings if isinstance(all_mappings, list) else []:
            src = m.get("sourceEntityDeveloperName", m.get("sourceObjectName", ""))
            tgt = m.get("targetEntityDeveloperName", m.get("targetObjectName", ""))
            if src == source_entity and tgt == target_entity:
                matches.append(m)

        if not matches:
            return {
                "error": "No mapping found",
                "source_entity": source_entity,
                "target_entity": target_entity,
                "hint": "Use get_data_stream_mappings to list all existing mappings",
            }

        deleted = []
        for m in matches:
            name = m.get("name", m.get("mappingName", ""))
            if not name:
                deleted.append({"error": "Could not determine mapping name", "mapping": m})
                continue
            url = f"{base_url}/services/data/v63.0/ssot/data-model-object-mappings/{name}"
            logger.info(f"Deleting DLO->DMO mapping '{name}'")
            resp = requests.delete(url, headers=headers, timeout=60)
            if resp.status_code == 204:
                deleted.append({"status": "deleted", "mapping_name": name})
            else:
                deleted.append({"error": f"HTTP {resp.status_code}", "detail": resp.text, "mapping_name": name})
        return {"source_entity": source_entity, "target_entity": target_entity, "results": deleted}

    url = f"{base_url}/services/data/v63.0/ssot/data-model-object-mappings/{mapping_name}"
    logger.info(f"Deleting DLO->DMO mapping '{mapping_name}'")
    resp = requests.delete(url, headers=headers, timeout=60)

    if resp.status_code == 204:
        return {"status": "deleted", "mapping_name": mapping_name}
    return {
        "error": f"Delete failed (HTTP {resp.status_code})",
        "detail": resp.text,
        "mapping_name": mapping_name,
    }


def create_custom_dmo(
    oauth_session: OAuthSession,
    name: str,
    label: str,
    category: str,
    fields: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Create a fully custom Data Model Object in Data Cloud.

    POST /services/data/v63.0/ssot/data-model-objects

    The API auto-adds system fields (DataSource, DataSourceObject,
    InternalOrganization) and Key Qualifier fields for primary keys.

    Args:
        name: API name for the DMO (alphanumeric + underscores, must start
              with a letter, must NOT start with 'ssot'). The API appends
              '__dlm' automatically.
        label: Human-readable display label.
        category: One of 'Profile', 'Engagement', 'Other'.
        fields: List of field definitions. Each dict must have:
            - name (str): Field API name (no __c suffix needed, added by API)
            - label (str): Display label
            - dataType (str): 'Text', 'Number', or 'DateTime'
            - isPrimaryKey (bool): Whether this is a primary key field
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "name": name,
        "label": label,
        "category": category,
        "fields": fields,
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-model-objects"

    logger.info(
        f"Creating custom DMO '{name}' (category={category}) "
        f"with {len(fields)} fields"
    )
    response = requests.post(url, json=payload, headers=headers, timeout=120)

    if response.status_code >= 300:
        return {
            "error_status": response.status_code,
            "error_body": response.text,
            "sent_payload": payload,
        }

    body = response.json()
    return {
        "status": "created",
        "dmo_name": body.get("name", ""),
        "dmo_id": body.get("id", ""),
        "label": body.get("label", ""),
        "category": body.get("category", ""),
        "fields": body.get("fields", []),
    }


def update_dlo_dmo_mapping(
    oauth_session: OAuthSession,
    mapping_name: str,
    field_mapping: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    Update an existing DLO-to-DMO mapping by deleting and recreating it with
    a new set of field mappings. The Data Cloud API does not support PATCH/PUT
    on mappings, so this performs an atomic delete + create.

    Fetches the current mapping first to extract source/target entities and
    compute a diff of changes. Auto-creates any missing custom DMO fields
    (via create_dlo_dmo_mapping).

    Args:
        mapping_name: The existing mapping's developerName
            (e.g., 'S3_Customer_Info_map_Individual_1778669048328')
        field_mapping: The new complete list of field mapping dicts, each with
            'sourceFieldDeveloperName' and 'targetFieldDeveloperName'.
            This REPLACES the existing mappings entirely (system fields like
            DataSource, InternalOrganization, KQ_ are auto-added by the API).
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # 1. Fetch the current mapping
    get_url = f"{base_url}/services/data/v63.0/ssot/data-model-object-mappings/{mapping_name}"
    logger.info(f"Fetching existing mapping '{mapping_name}' for update")
    get_resp = requests.get(get_url, headers=headers, timeout=60)

    if get_resp.status_code != 200:
        return {
            "error": f"Failed to fetch mapping '{mapping_name}' (HTTP {get_resp.status_code})",
            "detail": get_resp.text,
        }

    current = get_resp.json()
    source_entity = current["sourceEntityDeveloperName"]
    target_entity = current["targetEntityDeveloperName"]

    # Build diff for reporting
    old_user_fields = {
        (fm["sourceFieldDeveloperName"], fm["targetFieldDeveloperName"])
        for fm in current.get("fieldMappings", [])
        if not fm["sourceFieldDeveloperName"].startswith(("DataSource", "DataSourceObject", "InternalOrganization", "KQ_"))
    }
    new_user_fields = {
        (fm["sourceFieldDeveloperName"], fm["targetFieldDeveloperName"])
        for fm in field_mapping
    }
    added = new_user_fields - old_user_fields
    removed = old_user_fields - new_user_fields
    unchanged = old_user_fields & new_user_fields

    # 2. Delete the existing mapping
    logger.info(f"Deleting existing mapping '{mapping_name}' for update")
    del_url = f"{base_url}/services/data/v63.0/ssot/data-model-object-mappings/{mapping_name}"
    del_resp = requests.delete(del_url, headers=headers, timeout=60)

    if del_resp.status_code != 204:
        return {
            "error": f"Failed to delete old mapping (HTTP {del_resp.status_code})",
            "detail": del_resp.text,
            "mapping_name": mapping_name,
        }

    # 3. Recreate with the new field mappings (reuses create which auto-creates custom fields)
    logger.info(
        f"Recreating mapping {source_entity} -> {target_entity} "
        f"with {len(field_mapping)} field mappings"
    )
    create_result = create_dlo_dmo_mapping(
        oauth_session, source_entity, target_entity, field_mapping
    )

    # If create failed, report the problem clearly
    if "error_status" in create_result or "error" in create_result:
        create_result["warning"] = (
            f"Old mapping '{mapping_name}' was deleted but recreate failed. "
            f"You may need to create a new mapping manually."
        )
        return create_result

    return {
        "status": "updated",
        "old_mapping_name": mapping_name,
        "new_mapping_name": create_result.get("response", {}).get("developerName", ""),
        "source_entity": source_entity,
        "target_entity": target_entity,
        "diff": {
            "added": [{"source": s, "target": t} for s, t in sorted(added)],
            "removed": [{"source": s, "target": t} for s, t in sorted(removed)],
            "unchanged": len(unchanged),
        },
        "create_result": create_result,
    }


def create_dlo_dmo_mapping(
    oauth_session: OAuthSession,
    source_entity: str,
    target_entity: str,
    field_mapping: List[Dict[str, str]],
) -> Dict[str, Any]:
    """
    Create a DLO-to-DMO mapping in Data Cloud.

    Before creating the mapping, validates that all target fields exist on the
    DMO. Any target field that doesn't exist and isn't a standard ssot__ field
    is auto-created as a custom Text field on the DMO. This prevents the API
    from silently dropping field mappings for unregistered fields.

    POST /services/data/v63.0/ssot/data-model-object-mappings

    Args:
        source_entity: DLO developer name (e.g., 'test1__dll')
        target_entity: DMO developer name (e.g., 'ssot__AcademicYear__dlm')
        field_mapping: List of field mapping dicts, each with
            'sourceFieldDeveloperName' and 'targetFieldDeveloperName'
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Pre-flight: fetch DMO fields and auto-create any missing custom fields
    dmo_details_url = f"{base_url}/services/data/v63.0/ssot/data-model-objects/{target_entity}"
    dmo_resp = requests.get(dmo_details_url, headers=headers, timeout=60)

    auto_created_fields = []
    if dmo_resp.status_code == 200:
        dmo_data = dmo_resp.json()
        dmo_id = dmo_data.get("id")
        existing_fields = {f["name"] for f in dmo_data.get("fields", [])}

        target_fields = {
            fm["targetFieldDeveloperName"]
            for fm in field_mapping
        }
        missing = target_fields - existing_fields

        # Auto-create missing non-standard fields as custom DMO fields
        for field_api_name in missing:
            if field_api_name.startswith("ssot__") or field_api_name.startswith("KQ_"):
                continue
            if not field_api_name.endswith("__c"):
                continue

            label = field_api_name.replace("__c", "").replace("_", " ")
            logger.info(
                f"Auto-creating missing custom DMO field '{field_api_name}' "
                f"on {target_entity}"
            )
            result = create_custom_dmo_field(
                oauth_session,
                dmo_name=target_entity,
                field_name=field_api_name,
                field_label=label,
            )
            auto_created_fields.append(result)

    payload = {
        "sourceEntityDeveloperName": source_entity,
        "targetEntityDeveloperName": target_entity,
        "fieldMapping": field_mapping,
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-model-object-mappings"

    logger.info(
        f"Creating DLO->DMO mapping: {source_entity} -> {target_entity} "
        f"({len(field_mapping)} field mappings)"
    )
    response = requests.post(url, json=payload, headers=headers, timeout=120)

    if response.status_code >= 300:
        result = {
            "error_status": response.status_code,
            "error_body": response.text,
            "sent_payload": payload,
        }
        if auto_created_fields:
            result["auto_created_fields"] = auto_created_fields
        return result

    body = {}
    if response.status_code in (201, 204):
        try:
            body = response.json()
        except Exception:
            pass
    else:
        body = response.json()

    result = {"status": "created", "response": body, "sent_payload": payload}
    if auto_created_fields:
        result["auto_created_fields"] = auto_created_fields
    return result


def get_activations(
    oauth_session: OAuthSession,
    batch_size: int = 25,
    offset: int = 0,
    order_by: str = "createddate desc",
) -> Dict[str, Any]:
    """
    Get all segment activations from Data Cloud.

    Returns activations with details like activation target, status,
    refresh type, associated segment, and publish status.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/activations"
    params = {
        "batchSize": batch_size,
        "offset": offset,
        "orderByExpression": f"[{order_by}]",
    }

    logger.info(f"Fetching activations from {url}")
    response = requests.get(url, headers=headers, params=params, timeout=60)

    _handle_error_response(response)

    return response.json()


def get_activation_by_id(
    oauth_session: OAuthSession,
    activation_id: str,
) -> Dict[str, Any]:
    """
    Get details of a specific activation by ID.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/activations/{activation_id}"

    logger.info(f"Fetching activation {activation_id} from {url}")
    response = requests.get(url, headers=headers, timeout=60)

    _handle_error_response(response)

    return response.json()


def delete_activation(
    oauth_session: OAuthSession,
    activation_id: str,
) -> Dict[str, Any]:
    """
    Delete a specific activation by ID.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/activations/{activation_id}"

    logger.info(f"Deleting activation {activation_id} at {url}")
    response = requests.delete(url, headers=headers, timeout=60)

    _handle_error_response(response)

    if response.status_code == 204:
        return {"status": "deleted", "activationId": activation_id}
    return response.json()


def update_activation(
    oauth_session: OAuthSession,
    activation_id: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update a specific activation by ID (PATCH).

    Supports fields like refreshType, relatedDmoFiltersConfig,
    shouldExcludeDeletes, shouldExcludeUpdates, and staticDataConfig.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/activations/{activation_id}"

    logger.info(f"Updating activation {activation_id} at {url}")
    response = requests.patch(url, json=payload, headers=headers, timeout=120)

    _handle_error_response(response)

    if response.status_code == 204:
        return {"status": "updated", "activationId": activation_id}
    return response.json()


def get_ssot_connectors(oauth_session: OAuthSession) -> Dict[str, Any]:
    """
    Get all SSOT connectors (activation targets, marketing connectors, etc.)
    via the /ssot/connectors endpoint.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/connectors"

    logger.info(f"Fetching SSOT connectors from {url}")
    response = requests.get(url, headers=headers, timeout=60)

    _handle_error_response(response)

    return response.json()


def get_ssot_connector_metadata(
    oauth_session: OAuthSession,
    connector_type: str,
) -> Dict[str, Any]:
    """
    Get metadata for a specific SSOT connector type.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/connectors/{connector_type}"

    logger.info(f"Fetching connector metadata for {connector_type} from {url}")
    response = requests.get(url, headers=headers, timeout=60)

    _handle_error_response(response)

    return response.json()


def get_data_action_targets(oauth_session: OAuthSession) -> Dict[str, Any]:
    """
    Get all data action targets.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-action-targets"

    logger.info(f"Fetching data action targets from {url}")
    response = requests.get(url, headers=headers, timeout=60)

    _handle_error_response(response)

    return response.json()


def get_data_action_target_by_name(
    oauth_session: OAuthSession,
    api_name: str,
) -> Dict[str, Any]:
    """
    Get a specific data action target by API name.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-action-targets/{api_name}"

    logger.info(f"Fetching data action target {api_name} from {url}")
    response = requests.get(url, headers=headers, timeout=60)

    _handle_error_response(response)

    return response.json()


def create_data_action_target(
    oauth_session: OAuthSession,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Create a data action target (Core, MarketingCloud, or WebHook).
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-action-targets"

    logger.info(f"Creating data action target: {payload.get('apiName', 'unknown')}")
    response = requests.post(url, json=payload, headers=headers, timeout=120)

    _handle_error_response(response)

    if response.status_code == 204:
        return {"status": "created", "apiName": payload.get("apiName")}
    return response.json()


def delete_data_action_target(
    oauth_session: OAuthSession,
    api_name: str,
) -> Dict[str, Any]:
    """
    Delete a data action target by API name.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-action-targets/{api_name}"

    logger.info(f"Deleting data action target {api_name} at {url}")
    response = requests.delete(url, headers=headers, timeout=60)

    _handle_error_response(response)

    if response.status_code == 204:
        return {"status": "deleted", "apiName": api_name}
    return response.json()


def get_data_actions(oauth_session: OAuthSession) -> Dict[str, Any]:
    """
    Get all data actions from Data Cloud.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-actions"

    logger.info(f"Fetching data actions from {url}")
    response = requests.get(url, headers=headers, timeout=60)

    _handle_error_response(response)

    return response.json()


def create_data_action(
    oauth_session: OAuthSession,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Create a data action in Data Cloud.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-actions"

    logger.info(f"Creating data action: {payload.get('dataActionName', 'unknown')}")
    response = requests.post(url, json=payload, headers=headers, timeout=120)

    _handle_error_response(response)

    if response.status_code == 204:
        return {"status": "created", "dataActionName": payload.get("dataActionName")}
    return response.json()


def get_data_graph_metadata(oauth_session: OAuthSession) -> Dict[str, Any]:
    """
    Get metadata for all data graphs.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-graphs/metadata"

    logger.info(f"Fetching data graph metadata from {url}")
    response = requests.get(url, headers=headers, timeout=60)

    _handle_error_response(response)

    return response.json()


def create_data_lake_object(
    oauth_session: OAuthSession,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Create a Data Lake Object (DLO) in Data Cloud.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-lake-objects"

    logger.info(f"Creating DLO: {payload.get('name', 'unknown')}")
    response = requests.post(url, json=payload, headers=headers, timeout=120)

    _handle_error_response(response)

    if response.status_code == 204:
        return {"status": "created", "name": payload.get("name")}
    return response.json()


def update_data_lake_object(
    oauth_session: OAuthSession,
    dlo_identifier: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update a Data Lake Object (DLO) by record ID or developer name (PATCH).
    Can update label and add new fields.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-lake-objects/{dlo_identifier}"

    logger.info(f"Updating DLO {dlo_identifier} at {url}")
    response = requests.patch(url, json=payload, headers=headers, timeout=120)

    _handle_error_response(response)

    if response.status_code == 204:
        return {"status": "updated", "dlo": dlo_identifier}
    return response.json()


def delete_data_lake_object(
    oauth_session: OAuthSession,
    dlo_identifier: str,
) -> Dict[str, Any]:
    """
    Delete a Data Lake Object (DLO) by record ID or developer name.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-lake-objects/{dlo_identifier}"

    logger.info(f"Deleting DLO {dlo_identifier} at {url}")
    response = requests.delete(url, headers=headers, timeout=60)

    _handle_error_response(response)

    if response.status_code == 204:
        return {"status": "deleted", "dlo": dlo_identifier}
    return response.json()


def get_data_spaces(oauth_session: OAuthSession) -> Dict[str, Any]:
    """
    Get all data spaces.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-spaces"

    logger.info(f"Fetching data spaces from {url}")
    response = requests.get(url, headers=headers, timeout=60)

    _handle_error_response(response)

    return response.json()


def get_data_space_by_id(
    oauth_session: OAuthSession,
    id_or_name: str,
) -> Dict[str, Any]:
    """
    Get a specific data space by ID or name.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-spaces/{id_or_name}"

    logger.info(f"Fetching data space {id_or_name} from {url}")
    response = requests.get(url, headers=headers, timeout=60)

    _handle_error_response(response)

    return response.json()


def update_data_space(
    oauth_session: OAuthSession,
    id_or_name: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update a data space by ID or name (PATCH).
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-spaces/{id_or_name}"

    logger.info(f"Updating data space {id_or_name} at {url}")
    response = requests.patch(url, json=payload, headers=headers, timeout=120)

    _handle_error_response(response)

    if response.status_code == 204:
        return {"status": "updated", "dataSpace": id_or_name}
    return response.json()


def get_data_space_members(
    oauth_session: OAuthSession,
    id_or_name: str,
) -> Dict[str, Any]:
    """
    Get all members of a data space.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-spaces/{id_or_name}/members"

    logger.info(f"Fetching members for data space {id_or_name} from {url}")
    response = requests.get(url, headers=headers, timeout=60)

    _handle_error_response(response)

    return response.json()


def get_data_space_member(
    oauth_session: OAuthSession,
    id_or_name: str,
    member_object_name: str,
) -> Dict[str, Any]:
    """
    Get a specific member from a data space by object name.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-spaces/{id_or_name}/members/{member_object_name}"

    logger.info(f"Fetching member {member_object_name} from data space {id_or_name}")
    response = requests.get(url, headers=headers, timeout=60)

    _handle_error_response(response)

    return response.json()


def create_data_transform(
    oauth_session: OAuthSession,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Create a data transform (BATCH or STREAMING) in Data Cloud.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-transforms"

    logger.info(f"Creating data transform: {payload.get('name', 'unknown')}")
    response = requests.post(url, json=payload, headers=headers, timeout=120)

    _handle_error_response(response)

    if response.status_code == 204:
        return {"status": "created", "name": payload.get("name")}
    return response.json()


def update_data_transform(
    oauth_session: OAuthSession,
    name_or_id: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update a data transform by name or ID (PUT — full replacement).
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-transforms/{name_or_id}"

    logger.info(f"Updating data transform {name_or_id} at {url}")
    response = requests.put(url, json=payload, headers=headers, timeout=120)

    _handle_error_response(response)

    if response.status_code == 204:
        return {"status": "updated", "dataTransform": name_or_id}
    return response.json()


def delete_data_transform(
    oauth_session: OAuthSession,
    name_or_id: str,
) -> Dict[str, Any]:
    """
    Delete a data transform by name or ID.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-transforms/{name_or_id}"

    logger.info(f"Deleting data transform {name_or_id} at {url}")
    response = requests.delete(url, headers=headers, timeout=60)

    _handle_error_response(response)

    if response.status_code == 204:
        return {"status": "deleted", "dataTransform": name_or_id}
    return response.json()


def get_data_transform_run_history(
    oauth_session: OAuthSession,
    name_or_id: str,
) -> Dict[str, Any]:
    """
    Get run history for a specific data transform.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/data-transforms/{name_or_id}/run-history"

    logger.info(f"Fetching run history for data transform {name_or_id}")
    response = requests.get(url, headers=headers, timeout=60)

    _handle_error_response(response)

    return response.json()


def update_segment(
    oauth_session: OAuthSession,
    segment_api_name: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update a segment by API name (PATCH).
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/segments/{segment_api_name}"

    logger.info(f"Updating segment {segment_api_name} at {url}")
    response = requests.patch(url, json=payload, headers=headers, timeout=120)

    _handle_error_response(response)

    if response.status_code == 204:
        return {"status": "updated", "segment": segment_api_name}
    return response.json()


def delete_segment(
    oauth_session: OAuthSession,
    segment_api_name: str,
) -> Dict[str, Any]:
    """
    Delete a segment by API name.
    """
    base_url = oauth_session.get_instance_url()
    token = oauth_session.get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = f"{base_url}/services/data/v63.0/ssot/segments/{segment_api_name}"

    logger.info(f"Deleting segment {segment_api_name} at {url}")
    response = requests.delete(url, headers=headers, timeout=60)

    _handle_error_response(response)

    if response.status_code == 204:
        return {"status": "deleted", "segment": segment_api_name}
    return response.json()
