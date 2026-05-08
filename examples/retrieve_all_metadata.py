#!/usr/bin/env python3
"""
Retrieve all metadata from a Salesforce org using the REST API and Tooling API.
Saves results as JSON files in a 'metadata_output' directory.
"""
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oauth import OAuthConfig, OAuthSession

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

API_VERSION = "v63.0"

TOOLING_METADATA_TYPES = [
    ("ApexClass", "Id, Name, ApiVersion, Status, NamespacePrefix, LengthWithoutComments, CreatedDate, LastModifiedDate"),
    ("ApexTrigger", "Id, Name, ApiVersion, Status, TableEnumOrId, NamespacePrefix, CreatedDate, LastModifiedDate"),
    ("ApexPage", "Id, Name, ApiVersion, NamespacePrefix, Description, CreatedDate, LastModifiedDate"),
    ("ApexComponent", "Id, Name, ApiVersion, NamespacePrefix, Description, CreatedDate, LastModifiedDate"),
    ("AuraDefinitionBundle", "Id, DeveloperName, ApiVersion, NamespacePrefix, Description, CreatedDate, LastModifiedDate"),
    ("LightningComponentBundle", "Id, DeveloperName, ApiVersion, NamespacePrefix, Description, CreatedDate, LastModifiedDate"),
    ("Flow", "Id, DeveloperName, ActiveVersionId, LatestVersionId, ProcessType, Status, Description, ApiVersion, NamespacePrefix, CreatedDate, LastModifiedDate"),
    ("FlowDefinition", "Id, DeveloperName, ActiveVersionId, LatestVersionId, NamespacePrefix, Description"),
    ("CustomObject", "Id, DeveloperName, NamespacePrefix, ExternalSharingModel, Description, CreatedDate, LastModifiedDate"),
    ("CustomField", "Id, DeveloperName, NamespacePrefix, TableEnumOrId, DataType, FullName, Description, CreatedDate, LastModifiedDate"),
    ("ValidationRule", "Id, EntityDefinitionId, ValidationName, Active, Description, ErrorDisplayField, ErrorMessage, NamespacePrefix, CreatedDate, LastModifiedDate"),
    ("WorkflowRule", "Id, Name, TableEnumOrId, CreatedDate, LastModifiedDate"),
    ("CustomLabel", "Id, Name, Value, Category, Language, NamespacePrefix, CreatedDate, LastModifiedDate"),
    ("CustomMetadata", "Id, DeveloperName, NamespacePrefix, Language, Label, QualifiedApiName, CreatedDate, LastModifiedDate"),
    ("CustomPermission", "Id, DeveloperName, NamespacePrefix, Description, CreatedDate, LastModifiedDate"),
    ("PermissionSet", "Id, Name, Label, Description, IsOwnedByProfile, NamespacePrefix, Type, CreatedDate, LastModifiedDate"),
    ("Profile", "Id, Name, Description, UserType, CreatedDate, LastModifiedDate"),
    ("RecordType", "Id, Name, DeveloperName, SobjectType, IsActive, Description, NamespacePrefix, CreatedDate, LastModifiedDate"),
    ("Layout", "Id, Name, NamespacePrefix, TableEnumOrId, EntityDefinitionId, CreatedDate, LastModifiedDate"),
    ("EmailTemplate", "Id, Name, DeveloperName, NamespacePrefix, FolderId, Subject, Description, CreatedDate, LastModifiedDate"),
    ("StaticResource", "Id, Name, NamespacePrefix, ContentType, CacheControl, CreatedDate, LastModifiedDate"),
    ("RemoteSiteSetting", "Id, SiteName, EndpointUrl, IsActive, Description, CreatedDate, LastModifiedDate"),
    ("ConnectedApplication", "Id, Name, NamespacePrefix, CreatedDate, LastModifiedDate"),
    ("NamedCredential", "Id, DeveloperName, MasterLabel, Endpoint, NamespacePrefix, CreatedDate, LastModifiedDate"),
    ("ExternalDataSource", "Id, DeveloperName, MasterLabel, Type, NamespacePrefix, CreatedDate, LastModifiedDate"),
    ("CustomTab", "Id, DeveloperName, NamespacePrefix, SobjectName, Url, CreatedDate, LastModifiedDate"),
    ("ApexTestSuite", "Id, TestSuiteName, CreatedDate, LastModifiedDate"),
    ("CustomApplication", "Id, DeveloperName, Label, NamespacePrefix, Description, CreatedDate, LastModifiedDate"),
    ("QuickActionDefinition", "Id, DeveloperName, SobjectType, Type, NamespacePrefix, CreatedDate, LastModifiedDate"),
    ("CompactLayout", "Id, DeveloperName, SobjectType, NamespacePrefix, CreatedDate, LastModifiedDate"),
    ("PlatformEventChannel", "Id, DeveloperName, Label, NamespacePrefix, CreatedDate, LastModifiedDate"),
    ("CustomNotificationType", "Id, DeveloperName, CustomNotifTypeName, NamespacePrefix, CreatedDate, LastModifiedDate"),
]


def _get(session: OAuthSession, path: str, params: Optional[Dict] = None) -> Any:
    base_url = session.get_instance_url()
    token = session.get_token()
    url = f"{base_url}{path}"
    resp = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        params=params,
        timeout=120,
    )
    if resp.status_code >= 300:
        raise Exception(f"GET {path} failed ({resp.status_code}): {resp.text[:500]}")
    return resp.json()


def _tooling_query(session: OAuthSession, soql: str) -> List[Dict]:
    """Run a Tooling API SOQL query, handling pagination."""
    all_records: List[Dict] = []
    result = _get(session, f"/services/data/{API_VERSION}/tooling/query", {"q": soql})
    all_records.extend(result.get("records", []))
    while not result.get("done", True) and result.get("nextRecordsUrl"):
        result = _get(session, result["nextRecordsUrl"])
        all_records.extend(result.get("records", []))
    return all_records


def _soql_query(session: OAuthSession, soql: str) -> List[Dict]:
    """Run a standard SOQL query, handling pagination."""
    all_records: List[Dict] = []
    result = _get(session, f"/services/data/{API_VERSION}/query", {"q": soql})
    all_records.extend(result.get("records", []))
    while not result.get("done", True) and result.get("nextRecordsUrl"):
        result = _get(session, result["nextRecordsUrl"])
        all_records.extend(result.get("records", []))
    return all_records


def retrieve_describe_global(session: OAuthSession) -> Dict:
    logger.info("Retrieving global sObject describe...")
    return _get(session, f"/services/data/{API_VERSION}/sobjects/")


def retrieve_org_limits(session: OAuthSession) -> Dict:
    logger.info("Retrieving org limits...")
    return _get(session, f"/services/data/{API_VERSION}/limits/")


def retrieve_org_info(session: OAuthSession) -> List[Dict]:
    logger.info("Retrieving org information...")
    return _soql_query(
        session,
        "SELECT Id, Name, OrganizationType, InstanceName, IsSandbox, "
        "LanguageLocaleKey, DefaultLocaleSidKey, TimeZoneSidKey, "
        "FiscalYearStartMonth, NamespacePrefix "
        "FROM Organization LIMIT 1",
    )


def retrieve_users_summary(session: OAuthSession) -> List[Dict]:
    logger.info("Retrieving users summary...")
    return _soql_query(
        session,
        "SELECT Id, Username, Name, Email, Profile.Name, UserRole.Name, IsActive, "
        "UserType, LastLoginDate, CreatedDate "
        "FROM User WHERE IsActive = true ORDER BY LastLoginDate DESC NULLS LAST",
    )


def retrieve_installed_packages(session: OAuthSession) -> List[Dict]:
    logger.info("Retrieving installed packages...")
    try:
        return _tooling_query(
            session,
            "SELECT Id, SubscriberPackage.Name, SubscriberPackage.NamespacePrefix, "
            "SubscriberPackageVersion.MajorVersion, SubscriberPackageVersion.MinorVersion, "
            "SubscriberPackageVersion.PatchVersion, SubscriberPackageVersion.BuildNumber, "
            "SubscriberPackageVersion.Name "
            "FROM InstalledSubscriberPackage ORDER BY SubscriberPackage.Name",
        )
    except Exception as e:
        logger.warning(f"Could not retrieve installed packages: {e}")
        return []


def retrieve_sobject_details(session: OAuthSession, sobject_names: List[str]) -> Dict[str, Any]:
    """Retrieve full describe for a list of sObjects (custom objects + key standard objects)."""
    logger.info(f"Retrieving detailed descriptions for {len(sobject_names)} sObjects...")
    details = {}
    for i, name in enumerate(sobject_names):
        try:
            desc = _get(session, f"/services/data/{API_VERSION}/sobjects/{name}/describe/")
            details[name] = {
                "name": desc.get("name"),
                "label": desc.get("label"),
                "keyPrefix": desc.get("keyPrefix"),
                "custom": desc.get("custom"),
                "createable": desc.get("createable"),
                "queryable": desc.get("queryable"),
                "fieldCount": len(desc.get("fields", [])),
                "fields": [
                    {
                        "name": f.get("name"),
                        "label": f.get("label"),
                        "type": f.get("type"),
                        "custom": f.get("custom"),
                        "length": f.get("length"),
                        "referenceTo": f.get("referenceTo"),
                        "relationshipName": f.get("relationshipName"),
                        "nillable": f.get("nillable"),
                        "externalId": f.get("externalId"),
                        "unique": f.get("unique"),
                    }
                    for f in desc.get("fields", [])
                ],
                "recordTypeInfos": desc.get("recordTypeInfos", []),
                "childRelationships": [
                    {"childSObject": cr.get("childSObject"), "field": cr.get("field"), "relationshipName": cr.get("relationshipName")}
                    for cr in desc.get("childRelationships", [])
                ],
            }
            if (i + 1) % 25 == 0:
                logger.info(f"  ...described {i + 1}/{len(sobject_names)} objects")
        except Exception as e:
            logger.warning(f"  Could not describe {name}: {e}")
            details[name] = {"error": str(e)}
    return details


def retrieve_tooling_metadata(session: OAuthSession) -> Dict[str, List[Dict]]:
    """Query the Tooling API for all configured metadata types."""
    results = {}
    for type_name, fields in TOOLING_METADATA_TYPES:
        soql = f"SELECT {fields} FROM {type_name} ORDER BY CreatedDate DESC"
        logger.info(f"Querying Tooling API: {type_name}...")
        try:
            records = _tooling_query(session, soql)
            for r in records:
                r.pop("attributes", None)
            results[type_name] = records
            logger.info(f"  {type_name}: {len(records)} records")
        except Exception as e:
            logger.warning(f"  {type_name}: FAILED - {e}")
            results[type_name] = [{"error": str(e)}]
    return results


def save_json(data: Any, filepath: str):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.info(f"Saved: {filepath}")


def main():
    config = OAuthConfig.from_env()
    session = OAuthSession(config)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metadata_output", timestamp)
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"=== Salesforce Org Metadata Retrieval ===")
    logger.info(f"Output directory: {output_dir}")
    start = time.time()

    # 1. Org info
    try:
        org_info = retrieve_org_info(session)
        save_json(org_info, os.path.join(output_dir, "org_info.json"))
    except Exception as e:
        logger.error(f"Org info retrieval failed: {e}")

    # 2. Org limits
    try:
        limits = retrieve_org_limits(session)
        save_json(limits, os.path.join(output_dir, "org_limits.json"))
    except Exception as e:
        logger.error(f"Org limits retrieval failed: {e}")

    # 3. Global sObject describe
    try:
        global_desc = retrieve_describe_global(session)
        sobjects = global_desc.get("sobjects", [])
        save_json(sobjects, os.path.join(output_dir, "sobjects_global.json"))
        logger.info(f"Found {len(sobjects)} sObjects")

        # 4. Detailed describe for custom objects + key standard objects
        custom_objects = [s["name"] for s in sobjects if s.get("custom")]
        key_standard = [
            s["name"] for s in sobjects
            if s["name"] in (
                "Account", "Contact", "Lead", "Opportunity", "Case",
                "Task", "Event", "User", "Campaign", "CampaignMember",
                "OpportunityLineItem", "Product2", "Pricebook2", "PricebookEntry",
                "Order", "OrderItem", "Contract", "Quote", "QuoteLineItem",
                "ContentDocument", "ContentVersion", "Attachment",
                "EmailMessage", "FeedItem", "Dashboard", "Report",
            )
        ]
        objects_to_describe = sorted(set(custom_objects + key_standard))
        logger.info(f"Will describe {len(objects_to_describe)} objects ({len(custom_objects)} custom + {len(key_standard)} standard)")

        details = retrieve_sobject_details(session, objects_to_describe)
        save_json(details, os.path.join(output_dir, "sobject_details.json"))

        summary = {
            "totalSObjects": len(sobjects),
            "customObjects": len(custom_objects),
            "customObjectNames": sorted(custom_objects),
            "standardObjectsDescribed": sorted(key_standard),
        }
        save_json(summary, os.path.join(output_dir, "sobject_summary.json"))
    except Exception as e:
        logger.error(f"sObject retrieval failed: {e}")

    # 5. All Tooling API metadata
    try:
        tooling_metadata = retrieve_tooling_metadata(session)
        save_json(tooling_metadata, os.path.join(output_dir, "tooling_metadata.json"))

        meta_summary = {t: len(r) for t, r in tooling_metadata.items()}
        save_json(meta_summary, os.path.join(output_dir, "tooling_metadata_summary.json"))
    except Exception as e:
        logger.error(f"Tooling metadata retrieval failed: {e}")

    # 6. Active users
    try:
        users = retrieve_users_summary(session)
        for u in users:
            u.pop("attributes", None)
        save_json(users, os.path.join(output_dir, "active_users.json"))
        logger.info(f"Found {len(users)} active users")
    except Exception as e:
        logger.error(f"Users retrieval failed: {e}")

    # 7. Installed packages
    try:
        packages = retrieve_installed_packages(session)
        for p in packages:
            p.pop("attributes", None)
        save_json(packages, os.path.join(output_dir, "installed_packages.json"))
        logger.info(f"Found {len(packages)} installed packages")
    except Exception as e:
        logger.error(f"Installed packages retrieval failed: {e}")

    elapsed = time.time() - start
    logger.info(f"=== Complete in {elapsed:.1f}s === Output: {output_dir}")

    # Print a final summary
    print(f"\n{'='*60}")
    print(f"  Metadata retrieval complete!")
    print(f"  Output directory: {output_dir}")
    print(f"  Time elapsed: {elapsed:.1f}s")
    print(f"{'='*60}")
    output_files = sorted(os.listdir(output_dir))
    for fname in output_files:
        fpath = os.path.join(output_dir, fname)
        size_kb = os.path.getsize(fpath) / 1024
        print(f"  {fname:40s} {size_kb:>8.1f} KB")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
