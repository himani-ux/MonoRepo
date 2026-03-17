#!/usr/bin/env node

import sql from "mssql";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

// ============================
// MSSQL CONFIG
// ============================
const dbConfig = {
  user: "sa",
  password: "Yadavdy2002@",
  server: "127.0.0.1",   // ⚠ use IP not localhost (Linux issue sometimes)
  port: 1433,
  database: "ksm_inspection",
  options: {
    encrypt: false,
    trustServerCertificate: true,
    enableArithAbort: true,
  },
};

// ============================
// DB POOL
// ============================
const pool = await sql.connect(dbConfig);

// ============================
// MCP SERVER
// ============================
const server = new Server({
  name: "mssql-mcp",
  version: "1.0.0",
}, {
  capabilities: {
    tools: {},
  },
});

// ============================
// LIST TOOLS
// ============================
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "query_db",
        description: "Run a SQL query on MSSQL database",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string" },
          },
          required: ["query"],
        },
      },
    ],
  };
});

// ============================
// CALL TOOL
// ============================
server.setRequestHandler(CallToolRequestSchema, async (req) => {
  if (req.params.name === "query_db") {
    const result = await pool.request().query(req.params.arguments.query);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result.recordset, null, 2),
        },
      ],
    };
  }
});

// ============================
// START MCP
// ============================
const transport = new StdioServerTransport();
await server.connect(transport);