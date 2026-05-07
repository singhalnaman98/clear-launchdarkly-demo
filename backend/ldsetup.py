import os
import json
import launchdarkly_api
from launchdarkly_api.api import feature_flags_api, segments_api
from launchdarkly_api.models import (
    feature_flag_body, 
    variation, 
    patch_operation, 
    patch_with_comment,
    segment_body
)
from launchdarkly_api.rest import ApiException
from dotenv import load_dotenv

load_dotenv()

# 1. Configuration
API_TOKEN = os.environ.get('LD_API_KEY')
PROJECT_KEY = "naman-singhal-demo" 
ENV_KEY = "test" 
FILE_NAME = "flex-subscription-enabled.json"
SEGMENT_KEY = "clear-internal-qa"

if not API_TOKEN:
    raise ValueError("Please set the LD_API_KEY environment variable.")

# 2. Load the JSON data
try:
    with open(FILE_NAME, 'r') as f:
        flag_data = json.load(f)
except FileNotFoundError:
    raise FileNotFoundError(f"Could not find {FILE_NAME} in the current directory.")

# Initialize API Client
configuration = launchdarkly_api.Configuration()
configuration.api_key['ApiKey'] = API_TOKEN

with launchdarkly_api.ApiClient(configuration) as api_client:
    flags_instance = feature_flags_api.FeatureFlagsApi(api_client)
    segments_instance = segments_api.SegmentsApi(api_client)

    # ===================================================================
    # STEP 3: Create and Configure the Segment
    # ===================================================================
    
    # 3a. Create the bare segment first
    new_segment = segment_body.SegmentBody(
        name="Clear Internal QA",
        key=SEGMENT_KEY,
        description="Internal QA users for testing flex subscriptions"
    )

    try:
        print(f"Creating segment: {SEGMENT_KEY} in environment: {ENV_KEY}...")
        segments_instance.post_segment(
            project_key=PROJECT_KEY, 
            environment_key=ENV_KEY, 
            segment_body=new_segment
        )
        print("Base segment created successfully!")
    except ApiException as e:
        if e.status == 409:
            print(f"Segment creation skipped (it already exists).")
        else:
            print(f"Segment creation error ({e.status}): {e.reason}\nDetails: {e.body}")
    except Exception as e:
        print(f"Standard Python Error during segment creation: {e}")

    # 3b. Patch the segment to explicitly add the user targets using the legacy path
    seg_ops = [
        patch_operation.PatchOperation(
            op="add", 
            path="/included", 
            value=["user1", "user2", "user3"]
        )
    ]

    seg_patch_obj = patch_with_comment.PatchWithComment(
        comment="Adding specific users to QA segment", 
        patch=seg_ops
    )

    try:
        print(f"Adding user targets to segment: {SEGMENT_KEY}...")
        segments_instance.patch_segment(
            project_key=PROJECT_KEY,
            environment_key=ENV_KEY,
            segment_key=SEGMENT_KEY,
            patch_with_comment=seg_patch_obj
        )
        print(f"Users successfully added to {SEGMENT_KEY}!")
    except ApiException as e:
        print(f"❌ Error patching segment users ({e.status}): {e.reason}\nDetails: {e.body}")
    except Exception as e:
        print(f"❌ Standard Python Error during segment patching: {e}")


    # ===================================================================
    # STEP 4: Create the Base Feature Flag
    # ===================================================================
    variations = [
        variation.Variation(value=v['value'], name=v['name']) 
        for v in flag_data['variations']
    ]
    
    body = feature_flag_body.FeatureFlagBody(
        name=flag_data['name'],
        key=flag_data['key'],
        description=flag_data['description'],
        variations=variations,
        # Using a raw dictionary here prevents Pydantic validation mismatches
        client_side_availability={
            "usingMobileKey": flag_data['clientSideAvailability']['usingMobileKey'],
            "usingEnvironmentId": flag_data['clientSideAvailability']['usingEnvironmentId']
        },
        tags=flag_data['tags'],
        temporary=flag_data['temporary']
    )

    try:
        print(f"\nCreating flag: {flag_data['key']}...")
        flags_instance.post_feature_flag(PROJECT_KEY, body)
        print("Base flag created successfully!")
    except ApiException as e:
        if e.status == 409:
            print(f"Flag creation skipped (it already exists).")
        else:
            print(f"Flag creation error ({e.status}): {e.reason}\nDetails: {e.body}")
    except Exception as e:
        print(f"Standard Python Error during flag creation: {e}")

    # ===================================================================
    # STEP 5: Apply Environment-Specific Rules (Patch)
    # ===================================================================
    env_config = flag_data['environments'][ENV_KEY]
    
    # Strip database IDs from the rules to prevent conflicts
    cleaned_rules = []
    for rule in env_config['rules']:
        cleaned_rules.append({
            "variation": rule['variation'],
            "clauses": [
                {
                    "attribute": c['attribute'],
                    "op": c['op'],
                    "values": c['values'],
                    "negate": c['negate']
                } for c in rule['clauses']
            ]
        })

    patch_ops_raw = [
        {"op": "replace", "path": f"/environments/{ENV_KEY}/on", "value": env_config['on']},
        {"op": "replace", "path": f"/environments/{ENV_KEY}/offVariation", "value": env_config['offVariation']},
        {"op": "replace", "path": f"/environments/{ENV_KEY}/fallthrough/variation", "value": env_config['fallthrough']['variation']},
        {"op": "replace", "path": f"/environments/{ENV_KEY}/rules", "value": cleaned_rules}
    ]

    # Convert to formal PatchOperation models
    ops = [
        patch_operation.PatchOperation(op=p['op'], path=p['path'], value=p['value']) 
        for p in patch_ops_raw
    ]

    patch_obj = patch_with_comment.PatchWithComment(
        comment="Synchronizing segment and flag rules via script", 
        patch=ops
    )

    try:
        print(f"Applying targeting rules for environment: {ENV_KEY}...")
        flags_instance.patch_feature_flag(
            project_key=PROJECT_KEY, 
            feature_flag_key=flag_data['key'], 
            patch_with_comment=patch_obj
        )
        print("\n🚀 Success! Segment, Flag, and Rules are fully synchronized.")
    except ApiException as e:
        print(f"❌ Error patching flag rules ({e.status}): {e.reason}\nDetails: {e.body}")
    except Exception as e:
        print(f"❌ Standard Python Error during flag patching: {e}")