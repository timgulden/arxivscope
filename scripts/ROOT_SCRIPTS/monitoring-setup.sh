#!/bin/bash
# Azure Monitoring and Alerting Setup for DocScope/DocTrove

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
RESOURCE_GROUP="doctrove-prod"
LOCATION="eastus"
WORKSPACE_NAME="doctrove-workspace"
ACTION_GROUP_NAME="doctrove-alerts"

# Load environment variables
if [ -f .env.production ]; then
    source .env.production
else
    print_error ".env.production file not found. Please run azure-deploy.sh first."
    exit 1
fi

print_status "Setting up Azure monitoring and alerting..."

# Step 1: Create Log Analytics Workspace
print_status "Creating Log Analytics Workspace..."
az monitor log-analytics workspace create \
    --resource-group $RESOURCE_GROUP \
    --workspace-name $WORKSPACE_NAME \
    --location $LOCATION

WORKSPACE_ID=$(az monitor log-analytics workspace show \
    --resource-group $RESOURCE_GROUP \
    --workspace-name $WORKSPACE_NAME \
    --query "customerId" \
    --output tsv)

print_success "Log Analytics Workspace created: $WORKSPACE_NAME"

# Step 2: Create Application Insights
print_status "Creating Application Insights..."
az monitor app-insights component create \
    --resource-group $RESOURCE_GROUP \
    --app doctrove-insights \
    --location $LOCATION \
    --kind web \
    --application-type web \
    --workspace $WORKSPACE_ID

APP_INSIGHTS_KEY=$(az monitor app-insights component show \
    --resource-group $RESOURCE_GROUP \
    --app doctrove-insights \
    --query "instrumentationKey" \
    --output tsv)

print_success "Application Insights created: doctrove-insights"

# Step 3: Create Action Group for alerts
print_status "Creating Action Group for alerts..."
az monitor action-group create \
    --resource-group $RESOURCE_GROUP \
    --name $ACTION_GROUP_NAME \
    --short-name doctrove-alerts \
    --action email admin "admin@rand.org" \
    --action webhook webhook1 "https://webhook.site/your-webhook-url"

ACTION_GROUP_ID=$(az monitor action-group show \
    --resource-group $RESOURCE_GROUP \
    --name $ACTION_GROUP_NAME \
    --query "id" \
    --output tsv)

print_success "Action Group created: $ACTION_GROUP_NAME"

# Step 4: Create Database Alerts
print_status "Creating database performance alerts..."

# CPU Usage Alert
az monitor metrics alert create \
    --resource-group $RESOURCE_GROUP \
    --name "db-cpu-high" \
    --description "Database CPU usage is high" \
    --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.DBforPostgreSQL/flexibleServers/$DB_SERVER_NAME" \
    --condition "avg cpu_percent > 80" \
    --window-size 5m \
    --evaluation-frequency 1m \
    --action $ACTION_GROUP_ID

# Memory Usage Alert
az monitor metrics alert create \
    --resource-group $RESOURCE_GROUP \
    --name "db-memory-high" \
    --description "Database memory usage is high" \
    --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.DBforPostgreSQL/flexibleServers/$DB_SERVER_NAME" \
    --condition "avg memory_percent > 80" \
    --window-size 5m \
    --evaluation-frequency 1m \
    --action $ACTION_GROUP_ID

# Storage Usage Alert
az monitor metrics alert create \
    --resource-group $RESOURCE_GROUP \
    --name "db-storage-high" \
    --description "Database storage usage is high" \
    --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.DBforPostgreSQL/flexibleServers/$DB_SERVER_NAME" \
    --condition "avg storage_percent > 85" \
    --window-size 5m \
    --evaluation-frequency 1m \
    --action $ACTION_GROUP_ID

print_success "Database alerts created"

# Step 5: Create Container App Alerts
print_status "Creating container app alerts..."

# API Response Time Alert
az monitor metrics alert create \
    --resource-group $RESOURCE_GROUP \
    --name "api-response-slow" \
    --description "API response time is slow" \
    --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.App/containerApps/doctrove-api" \
    --condition "avg httpServerDuration > 5000" \
    --window-size 5m \
    --evaluation-frequency 1m \
    --action $ACTION_GROUP_ID

# Container App CPU Alert
az monitor metrics alert create \
    --resource-group $RESOURCE_GROUP \
    --name "container-cpu-high" \
    --description "Container CPU usage is high" \
    --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.App/containerApps/doctrove-api" \
    --condition "avg cpuPercentage > 80" \
    --window-size 5m \
    --evaluation-frequency 1m \
    --action $ACTION_GROUP_ID

print_success "Container app alerts created"

# Step 6: Create Log-based Alerts
print_status "Creating log-based alerts..."

# Error Rate Alert
az monitor scheduled-query create \
    --resource-group $RESOURCE_GROUP \
    --name "error-rate-high" \
    --description "Error rate is high" \
    --scopes $WORKSPACE_ID \
    --query "ContainerAppConsoleLogs_CL | where Log_s contains 'ERROR' | summarize count() by bin(TimeGenerated, 5m)" \
    --condition "count > 10" \
    --window-size 5m \
    --evaluation-frequency 1m \
    --action $ACTION_GROUP_ID

print_success "Log-based alerts created"

# Step 7: Create Dashboard
print_status "Creating monitoring dashboard..."
cat > dashboard.json << EOF
{
  "lenses": {
    "0": {
      "order": 0,
      "parts": {
        "0": {
          "position": {
            "x": 0,
            "y": 0,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "Query": "ContainerAppConsoleLogs_CL | summarize count() by bin(TimeGenerated, 1h)",
                "PartTitle": "API Requests per Hour"
              }
            }
          }
        },
        "1": {
          "position": {
            "x": 6,
            "y": 0,
            "colSpan": 6,
            "rowSpan": 4
          },
          "metadata": {
            "inputs": [],
            "type": "Extension/Microsoft_OperationsManagementSuite_Workspace/PartType/LogsDashboardPart",
            "settings": {
              "content": {
                "Query": "ContainerAppConsoleLogs_CL | where Log_s contains 'ERROR' | summarize count() by bin(TimeGenerated, 1h)",
                "PartTitle": "Errors per Hour"
              }
            }
          }
        }
      }
    }
  },
  "metadata": {
    "model": {
      "timeRange": {
        "value": {
          "relative": {
            "duration": 24,
            "timeUnit": 1
          }
        },
        "type": "MsPortalFx.Composition.Configuration.ValueTypes.TimeRange"
      },
      "filterLocale": {
        "value": "en-us"
      },
      "filters": {
        "value": {
          "MsPortalFx_TimeRange": {
            "model": {
              "format": "utc",
              "value": {
                "relative": {
                  "duration": 24,
                  "timeUnit": 1
                }
              }
            },
            "displayCache": {
              "name": "UTC Time",
              "value": "Past 24 hours"
            },
            "filteredPartIds": {
              "0": "0"
            }
          }
        }
      }
    }
  },
  "name": "DocTrove Monitoring Dashboard",
  "version": "1.0"
}
EOF

az portal dashboard create \
    --resource-group $RESOURCE_GROUP \
    --name "doctrove-dashboard" \
    --location $LOCATION \
    --input-path dashboard.json

print_success "Monitoring dashboard created"

# Step 8: Create monitoring configuration file
print_status "Creating monitoring configuration..."
cat > monitoring-config.env << EOF
# Monitoring Configuration
WORKSPACE_ID=$WORKSPACE_ID
APP_INSIGHTS_KEY=$APP_INSIGHTS_KEY
ACTION_GROUP_ID=$ACTION_GROUP_ID

# Log Analytics Workspace
WORKSPACE_NAME=$WORKSPACE_NAME

# Application Insights
APP_INSIGHTS_NAME=doctrove-insights

# Dashboard
DASHBOARD_NAME=doctrove-dashboard
EOF

print_success "Monitoring configuration created: monitoring-config.env"

# Summary
print_success "Azure monitoring and alerting setup completed!"
echo ""
echo "Monitoring Resources:"
echo "Log Analytics Workspace: $WORKSPACE_NAME"
echo "Application Insights: doctrove-insights"
echo "Action Group: $ACTION_GROUP_NAME"
echo "Dashboard: doctrove-dashboard"
echo ""
echo "Alerts Created:"
echo "- Database CPU usage > 80%"
echo "- Database memory usage > 80%"
echo "- Database storage usage > 85%"
echo "- API response time > 5 seconds"
echo "- Container CPU usage > 80%"
echo "- Error rate > 10 errors per 5 minutes"
echo ""
echo "Next steps:"
echo "1. Update the webhook URL in the Action Group for notifications"
echo "2. Configure additional alerts as needed"
echo "3. Set up custom dashboards for specific metrics"
echo "4. Configure log retention policies" 