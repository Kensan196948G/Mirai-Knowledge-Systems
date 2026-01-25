# Mirai Knowledge Systems - API Documentation

## Overview
This document provides comprehensive API documentation for the Mirai Knowledge Systems platform.

## Authentication
All API endpoints require JWT authentication via Bearer token in Authorization header.

### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

### Refresh Token
```http
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
```

## Knowledge Management

### Get Knowledge List
```http
GET /api/v1/knowledge?category=string&status=string&search=string&limit=50&offset=0
Authorization: Bearer <token>
```

### Create Knowledge
```http
POST /api/v1/knowledge
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "string",
  "content": "string",
  "category": "string",
  "status": "draft|published|archived"
}
```

### Update Knowledge
```http
PUT /api/v1/knowledge/{id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "string",
  "content": "string",
  "category": "string",
  "status": "string"
}
```

### Delete Knowledge
```http
DELETE /api/v1/knowledge/{id}
Authorization: Bearer <token>
```

## File Management

### Upload File
```http
POST /api/v1/files/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <binary_data>
path: "optional/folder/path"
```

### Download File
```http
GET /api/v1/files/{file_id}
Authorization: Bearer <token>
```

### Get File List
```http
GET /api/v1/files
Authorization: Bearer <token>
```

## Microsoft 365 Integration

### Check Auth Status
```http
GET /api/v1/microsoft365/auth/status
Authorization: Bearer <token>
```

### Get Files
```http
GET /api/v1/microsoft365/files?service=onedrive|sharepoint&path=/folder
Authorization: Bearer <token>
```

### Upload to Microsoft 365
```http
POST /api/v1/microsoft365/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <binary_data>
service: "onedrive|sharepoint"
path: "/destination/folder"
```

## Dashboard & Analytics

### Get Statistics
```http
GET /api/v1/dashboard/stats
Authorization: Bearer <token>
```

### Get Recommendations
```http
GET /api/v1/recommendations/personalized?limit=10
Authorization: Bearer <token>
```

## Error Responses
All endpoints return standardized error responses:

```json
{
  "success": false,
  "message": "Error description",
  "error_code": "ERROR_CODE"
}
```

## Rate Limiting
- Authenticated requests: 100/minute
- File uploads: 10/minute
- Microsoft 365 operations: 50/minute