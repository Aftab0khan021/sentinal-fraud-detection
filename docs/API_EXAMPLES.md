# SentinAL API Usage Examples

## Table of Contents
- [Authentication](#authentication)
- [Fraud Detection](#fraud-detection)
- [Graph Visualization](#graph-visualization)
- [Python SDK](#python-sdk)
- [JavaScript/TypeScript](#javascripttypescript)
- [cURL Examples](#curl-examples)

---

## Authentication

### Login
Get access and refresh tokens for API access.

**Python:**
```python
import requests

response = requests.post(
    "https://api.sentinal.ai/api/auth/login",
    json={
        "email": "analyst@sentinal.ai",
        "password": "SecurePass123!"
    }
)

tokens = response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

print(f"Access Token: {access_token}")
```

**JavaScript:**
```javascript
const response = await fetch('https://api.sentinal.ai/api/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'analyst@sentinal.ai',
    password: 'SecurePass123!'
  })
});

const { access_token, refresh_token } = await response.json();
console.log('Access Token:', access_token);
```

**cURL:**
```bash
curl -X POST https://api.sentinal.ai/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "analyst@sentinal.ai",
    "password": "SecurePass123!"
  }'
```

### Refresh Token
Get a new access token using refresh token.

**Python:**
```python
response = requests.post(
    "https://api.sentinal.ai/api/auth/refresh",
    json={"refresh_token": refresh_token}
)

new_access_token = response.json()["access_token"]
```

**JavaScript:**
```javascript
const response = await fetch('https://api.sentinal.ai/api/auth/refresh', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    refresh_token: refreshToken
  })
});

const { access_token } = await response.json();
```

---

## Fraud Detection

### Analyze Transaction
Analyze a user's transaction for fraud using GNN + GraphRAG.

**Python:**
```python
headers = {"Authorization": f"Bearer {access_token}"}

response = requests.post(
    "https://api.sentinal.ai/api/analyze/77",
    headers=headers
)

result = response.json()

print(f"User ID: {result['user_id']}")
print(f"Fraud Score: {result['score']}")
print(f"Is Fraud: {result['is_fraud']}")
print(f"Explanation: {result['agent_report']}")
```

**JavaScript:**
```javascript
const response = await fetch('https://api.sentinal.ai/api/analyze/77', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});

const result = await response.json();

console.log('User ID:', result.user_id);
console.log('Fraud Score:', result.score);
console.log('Is Fraud:', result.is_fraud);
console.log('Explanation:', result.agent_report);
```

**cURL:**
```bash
curl -X POST https://api.sentinal.ai/api/analyze/77 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Batch Analysis
Analyze multiple users in parallel.

**Python:**
```python
import asyncio
import aiohttp

async def analyze_user(session, user_id, token):
    async with session.post(
        f"https://api.sentinal.ai/api/analyze/{user_id}",
        headers={"Authorization": f"Bearer {token}"}
    ) as response:
        return await response.json()

async def batch_analyze(user_ids, token):
    async with aiohttp.ClientSession() as session:
        tasks = [analyze_user(session, uid, token) for uid in user_ids]
        results = await asyncio.gather(*tasks)
        return results

# Analyze users 0-9
user_ids = range(10)
results = asyncio.run(batch_analyze(user_ids, access_token))

for result in results:
    print(f"User {result['user_id']}: {result['score']} - {result['is_fraud']}")
```

**JavaScript:**
```javascript
async function batchAnalyze(userIds, accessToken) {
  const promises = userIds.map(userId =>
    fetch(`https://api.sentinal.ai/api/analyze/${userId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }).then(r => r.json())
  );
  
  return await Promise.all(promises);
}

const userIds = Array.from({length: 10}, (_, i) => i);
const results = await batchAnalyze(userIds, accessToken);

results.forEach(result => {
  console.log(`User ${result.user_id}: ${result.score} - ${result.is_fraud}`);
});
```

---

## Graph Visualization

### Get Full Graph Data
Retrieve the complete transaction graph for visualization.

**Python:**
```python
response = requests.get(
    "https://api.sentinal.ai/api/graph",
    headers={"Authorization": f"Bearer {access_token}"}
)

graph = response.json()

print(f"Nodes: {len(graph['nodes'])}")
print(f"Links: {len(graph['links'])}")

# Example: Find high-risk nodes
high_risk = [
    node for node in graph['nodes'] 
    if node['fraud_probability'] > 0.8
]
print(f"High-risk nodes: {len(high_risk)}")
```

**JavaScript:**
```javascript
const response = await fetch('https://api.sentinal.ai/api/graph', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const graph = await response.json();

console.log('Nodes:', graph.nodes.length);
console.log('Links:', graph.links.length);

// Find high-risk nodes
const highRisk = graph.nodes.filter(node => node.fraud_probability > 0.8);
console.log('High-risk nodes:', highRisk.length);
```

---

## Python SDK

### Complete Example
```python
import requests
from typing import Dict, List, Optional

class SentinALClient:
    """Python SDK for SentinAL Fraud Detection API"""
    
    def __init__(self, base_url: str = "https://api.sentinal.ai"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
    
    def login(self, email: str, password: str) -> Dict:
        """Authenticate and get tokens"""
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"email": email, "password": password}
        )
        response.raise_for_status()
        
        data = response.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        return data
    
    def _get_headers(self) -> Dict:
        """Get authorization headers"""
        if not self.access_token:
            raise ValueError("Not authenticated. Call login() first.")
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def analyze(self, user_id: int) -> Dict:
        """Analyze user for fraud"""
        response = requests.post(
            f"{self.base_url}/api/analyze/{user_id}",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    def get_graph(self) -> Dict:
        """Get full transaction graph"""
        response = requests.get(
            f"{self.base_url}/api/graph",
            headers=self._get_headers()
        )
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict:
        """Check API health"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

# Usage
client = SentinALClient()
client.login("analyst@sentinal.ai", "SecurePass123!")

# Analyze user
result = client.analyze(77)
print(f"Fraud probability: {result['score']}")

# Get graph
graph = client.get_graph()
print(f"Graph has {len(graph['nodes'])} nodes")
```

---

## JavaScript/TypeScript

### TypeScript SDK
```typescript
interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

interface AnalyzeResponse {
  user_id: number;
  score: string;
  is_fraud: boolean;
  reason: string;
  agent_report: string;
}

interface GraphNode {
  id: string;
  is_fraud: boolean;
  risk_score: number;
  fraud_probability: number;
}

interface GraphLink {
  source: string;
  target: string;
  amount: number;
  is_laundering: boolean;
}

interface GraphResponse {
  nodes: GraphNode[];
  links: GraphLink[];
}

class SentinALClient {
  private baseUrl: string;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor(baseUrl: string = 'https://api.sentinal.ai') {
    this.baseUrl = baseUrl;
  }

  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await fetch(`${this.baseUrl}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      throw new Error(`Login failed: ${response.statusText}`);
    }

    const data: LoginResponse = await response.json();
    this.accessToken = data.access_token;
    this.refreshToken = data.refresh_token;
    return data;
  }

  private getHeaders(): HeadersInit {
    if (!this.accessToken) {
      throw new Error('Not authenticated. Call login() first.');
    }
    return {
      'Authorization': `Bearer ${this.accessToken}`,
      'Content-Type': 'application/json',
    };
  }

  async analyze(userId: number): Promise<AnalyzeResponse> {
    const response = await fetch(`${this.baseUrl}/api/analyze/${userId}`, {
      method: 'POST',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Analysis failed: ${response.statusText}`);
    }

    return await response.json();
  }

  async getGraph(): Promise<GraphResponse> {
    const response = await fetch(`${this.baseUrl}/api/graph`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Failed to get graph: ${response.statusText}`);
    }

    return await response.json();
  }

  async healthCheck(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/health`);
    
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }

    return await response.json();
  }
}

// Usage
const client = new SentinALClient();
await client.login('analyst@sentinal.ai', 'SecurePass123!');

const result = await client.analyze(77);
console.log(`Fraud probability: ${result.score}`);

const graph = await client.getGraph();
console.log(`Graph has ${graph.nodes.length} nodes`);
```

---

## cURL Examples

### Complete Workflow
```bash
#!/bin/bash

# 1. Login
LOGIN_RESPONSE=$(curl -s -X POST https://api.sentinal.ai/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "analyst@sentinal.ai",
    "password": "SecurePass123!"
  }')

# Extract access token
ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')
echo "Access Token: $ACCESS_TOKEN"

# 2. Analyze user
ANALYSIS=$(curl -s -X POST https://api.sentinal.ai/api/analyze/77 \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Analysis Result:"
echo $ANALYSIS | jq '.'

# 3. Get graph data
GRAPH=$(curl -s https://api.sentinal.ai/api/graph \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Graph Data:"
echo $GRAPH | jq '{node_count: (.nodes | length), link_count: (.links | length)}'

# 4. Health check
HEALTH=$(curl -s https://api.sentinal.ai/health)
echo "Health Status:"
echo $HEALTH | jq '.'
```

### Error Handling
```bash
# Function to make authenticated request
make_request() {
  local endpoint=$1
  local method=${2:-GET}
  
  response=$(curl -s -w "\n%{http_code}" -X $method \
    "https://api.sentinal.ai$endpoint" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  
  http_code=$(echo "$response" | tail -n1)
  body=$(echo "$response" | sed '$d')
  
  if [ $http_code -eq 200 ] || [ $http_code -eq 201 ]; then
    echo "$body"
  else
    echo "Error: HTTP $http_code"
    echo "$body" | jq '.'
    return 1
  fi
}

# Usage
make_request "/api/analyze/77" "POST"
```

---

## Integration Examples

### Webhook Integration
```python
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# SentinAL client
sentinal_token = "YOUR_ACCESS_TOKEN"

@app.route('/webhook/transaction', methods=['POST'])
def analyze_transaction():
    """Webhook endpoint for real-time fraud detection"""
    
    # Get transaction data
    transaction = request.json
    user_id = transaction.get('user_id')
    
    # Analyze with SentinAL
    response = requests.post(
        f"https://api.sentinal.ai/api/analyze/{user_id}",
        headers={"Authorization": f"Bearer {sentinal_token}"}
    )
    
    result = response.json()
    
    # Take action based on result
    if result['is_fraud']:
        # Block transaction
        return jsonify({
            "action": "block",
            "reason": result['reason'],
            "score": result['score']
        })
    else:
        # Allow transaction
        return jsonify({
            "action": "allow",
            "score": result['score']
        })

if __name__ == '__main__':
    app.run(port=5000)
```

### Scheduled Batch Processing
```python
import schedule
import time
from sentinal_client import SentinALClient

client = SentinALClient()
client.login("analyst@sentinal.ai", "SecurePass123!")

def daily_fraud_scan():
    """Scan all users daily for fraud"""
    print("Starting daily fraud scan...")
    
    # Get list of users to scan
    user_ids = range(100)  # Example: scan users 0-99
    
    high_risk_users = []
    
    for user_id in user_ids:
        try:
            result = client.analyze(user_id)
            
            if result['is_fraud']:
                high_risk_users.append({
                    'user_id': user_id,
                    'score': result['score'],
                    'reason': result['reason']
                })
        except Exception as e:
            print(f"Error analyzing user {user_id}: {e}")
    
    # Send report
    print(f"Found {len(high_risk_users)} high-risk users")
    # Send email/Slack notification with results

# Schedule daily at 2 AM
schedule.every().day.at("02:00").do(daily_fraud_scan)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## Rate Limiting

All endpoints are rate-limited. Handle rate limit errors gracefully:

**Python:**
```python
import time

def analyze_with_retry(client, user_id, max_retries=3):
    """Analyze with automatic retry on rate limit"""
    for attempt in range(max_retries):
        try:
            return client.analyze(user_id)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # Rate limited - wait and retry
                retry_after = int(e.response.headers.get('Retry-After', 60))
                print(f"Rate limited. Retrying after {retry_after}s...")
                time.sleep(retry_after)
            else:
                raise
    
    raise Exception(f"Failed after {max_retries} retries")
```

---

## Best Practices

1. **Token Management**
   - Store tokens securely (environment variables, secrets manager)
   - Refresh tokens before they expire
   - Handle 401 errors by refreshing token

2. **Error Handling**
   - Always check response status codes
   - Handle rate limiting (429) with exponential backoff
   - Log errors for debugging

3. **Performance**
   - Use batch requests when analyzing multiple users
   - Cache results when appropriate
   - Use async/await for parallel requests

4. **Security**
   - Never log access tokens
   - Use HTTPS only
   - Rotate credentials regularly
   - Validate SSL certificates

---

## Support

- **Documentation**: https://docs.sentinal.ai
- **API Reference**: https://api.sentinal.ai/docs
- **Support**: support@sentinal.ai
- **Status Page**: https://status.sentinal.ai
