#!/usr/bin/env node

/**
 * Feishu (Lark) Open API CLI for Claude Code
 * 
 * Usage: node feishu.mjs <tool> <action> [--param value ...]
 * 
 * Env vars: FEISHU_APP_ID, FEISHU_APP_SECRET
 */

import path from "node:path";

const BASE_URL = "https://open.feishu.cn/open-apis";

// --- Auth ---
let cachedToken = null;
let tokenExpiry = 0;

async function getToken() {
  if (cachedToken && Date.now() < tokenExpiry) return cachedToken;
  const appId = process.env.FEISHU_APP_ID;
  const secret = process.env.FEISHU_APP_SECRET;
  if (!appId || !secret) {
    console.error("Error: FEISHU_APP_ID and FEISHU_APP_SECRET must be set");
    process.exit(1);
  }
  const res = await fetch(`${BASE_URL}/auth/v3/tenant_access_token/internal`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ app_id: appId, app_secret: secret }),
  });
  const data = await res.json();
  if (data.code !== 0) throw new Error(`Auth failed: ${data.msg}`);
  cachedToken = data.tenant_access_token;
  tokenExpiry = Date.now() + (data.expire - 60) * 1000;
  return cachedToken;
}

async function api(method, path, { params, body } = {}) {
  const token = await getToken();
  let url = `${BASE_URL}${path}`;
  if (params) {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) if (v != null) qs.set(k, String(v));
    const s = qs.toString();
    if (s) url += `?${s}`;
  }
  const opts = {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  };
  if (body != null) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  const data = await res.json();
  if (data.code !== 0) throw new Error(`[${method} ${path}] code=${data.code} msg=${data.msg}`);
  return data.data;
}

// --- Arg parsing ---
function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next && !next.startsWith("--")) {
        try { args[key] = JSON.parse(next); } catch { args[key] = next; }
        i++;
      } else {
        args[key] = true;
      }
    }
  }
  return args;
}

// --- Doc ---
const doc = {
  async read({ doc_token }) {
    const [content, info, blocks] = await Promise.all([
      api("GET", `/docx/v1/documents/${doc_token}/raw_content`),
      api("GET", `/docx/v1/documents/${doc_token}`),
      api("GET", `/docx/v1/documents/${doc_token}/blocks`),
    ]);
    const items = blocks.items ?? [];
    const blockTypes = {};
    for (const b of items) {
      const t = b.block_type ?? 0;
      blockTypes[t] = (blockTypes[t] || 0) + 1;
    }
    return {
      title: info.document?.title,
      content: content.content,
      block_count: items.length,
      block_types: blockTypes,
    };
  },

  async write({ doc_token, content }) {
    // Clear existing content
    const existing = await api("GET", `/docx/v1/documents/${doc_token}/blocks`);
    const childIds = (existing.items ?? [])
      .filter((b) => b.parent_id === doc_token && b.block_type !== 1)
      .map((b) => b.block_id);
    if (childIds.length > 0) {
      await api("DELETE", `/docx/v1/documents/${doc_token}/blocks/batch_delete`, {
        body: { start_index: 0, end_index: childIds.length },
      });
    }
    // Convert markdown and insert
    const converted = await api("POST", "/docx/v1/documents/convert", {
      body: { content_type: "markdown", content },
    });
    if (converted.blocks?.length > 0) {
      await api("POST", `/docx/v1/documents/${doc_token}/blocks/${doc_token}/children`, {
        body: {
          children: converted.blocks,
          children_id: converted.first_level_block_ids,
        },
      });
    }
    return { success: true, blocks_added: converted.blocks?.length ?? 0 };
  },

  async append({ doc_token, content }) {
    const converted = await api("POST", "/docx/v1/documents/convert", {
      body: { content_type: "markdown", content },
    });
    if (converted.blocks?.length > 0) {
      await api("POST", `/docx/v1/documents/${doc_token}/blocks/${doc_token}/children`, {
        body: {
          children: converted.blocks,
          children_id: converted.first_level_block_ids,
        },
      });
    }
    return { success: true, blocks_added: converted.blocks?.length ?? 0 };
  },

  async create({ title, folder_token }) {
    const data = await api("POST", "/docx/v1/documents", {
      body: { title, ...(folder_token ? { folder_token } : {}) },
    });
    return {
      document_id: data.document?.document_id,
      title: data.document?.title,
      url: `https://feishu.cn/docx/${data.document?.document_id}`,
    };
  },

  async list_blocks({ doc_token }) {
    const data = await api("GET", `/docx/v1/documents/${doc_token}/blocks`);
    return { blocks: data.items ?? [] };
  },

  async get_block({ doc_token, block_id }) {
    const data = await api("GET", `/docx/v1/documents/${doc_token}/blocks/${block_id}`);
    return { block: data.block };
  },

  async update_block({ doc_token, block_id, content }) {
    await api("PATCH", `/docx/v1/documents/${doc_token}/blocks/${block_id}`, {
      body: { update_text_elements: { elements: [{ text_run: { content } }] } },
    });
    return { success: true, block_id };
  },

  async delete_block({ doc_token, block_id }) {
    // Find parent and index
    const block = await api("GET", `/docx/v1/documents/${doc_token}/blocks/${block_id}`);
    const parentId = block.block?.parent_id ?? doc_token;
    const children = await api("GET", `/docx/v1/documents/${doc_token}/blocks/${parentId}/children`);
    const index = (children.items ?? []).findIndex((b) => b.block_id === block_id);
    if (index === -1) throw new Error("Block not found in parent's children");
    await api("DELETE", `/docx/v1/documents/${doc_token}/blocks/${parentId}/batch_delete`, {
      body: { start_index: index, end_index: index + 1 },
    });
    return { success: true, deleted_block_id: block_id };
  },

  async create_table({ doc_token, row_size, column_size, column_width }) {
    const data = await api("POST", `/docx/v1/documents/${doc_token}/blocks/${doc_token}/children`, {
      body: {
        children: [{
          block_type: 31,
          table: {
            property: {
              row_size,
              column_size,
              ...(column_width ? { column_width } : {}),
            },
          },
        }],
      },
    });
    const tableBlock = (data.children ?? []).find((b) => b.block_type === 31);
    return {
      success: true,
      table_block_id: tableBlock?.block_id,
      row_size,
      column_size,
    };
  },

  async write_table_cells({ doc_token, table_block_id, values }) {
    // Get table to find cell IDs
    const table = await api("GET", `/docx/v1/documents/${doc_token}/blocks/${table_block_id}`);
    const cellIds = table.block?.table?.cells ?? [];
    const rows = table.block?.table?.property?.row_size ?? 0;
    const cols = table.block?.table?.property?.column_size ?? 0;
    let written = 0;
    for (let r = 0; r < Math.min(values.length, rows); r++) {
      for (let c = 0; c < Math.min(values[r]?.length ?? 0, cols); c++) {
        const cellId = cellIds[r * cols + c];
        if (!cellId) continue;
        // Clear cell
        const cellChildren = await api("GET", `/docx/v1/documents/${doc_token}/blocks/${cellId}/children`);
        const existing = cellChildren.items ?? [];
        if (existing.length > 0) {
          await api("DELETE", `/docx/v1/documents/${doc_token}/blocks/${cellId}/batch_delete`, {
            body: { start_index: 0, end_index: existing.length },
          });
        }
        // Write value
        const converted = await api("POST", "/docx/v1/documents/convert", {
          body: { content_type: "markdown", content: values[r][c] ?? "" },
        });
        if (converted.blocks?.length > 0) {
          await api("POST", `/docx/v1/documents/${doc_token}/blocks/${cellId}/children`, {
            body: { children: converted.blocks },
          });
        }
        written++;
      }
    }
    return { success: true, cells_written: written };
  },

  async create_table_with_values({ doc_token, row_size, column_size, values, column_width }) {
    const table = await doc.create_table({ doc_token, row_size, column_size, column_width });
    if (!table.table_block_id) throw new Error("Table creation failed");
    const cells = await doc.write_table_cells({ doc_token, table_block_id: table.table_block_id, values });
    return { ...table, cells_written: cells.cells_written };
  },

  async upload_image({ doc_token, url, file_path }) {
    // Create image block
    const blockData = await api("POST", `/docx/v1/documents/${doc_token}/blocks/${doc_token}/children`, {
      body: { children: [{ block_type: 27, image: {} }] },
    });
    const imageBlockId = (blockData.children ?? []).find((b) => b.block_type === 27)?.block_id;
    if (!imageBlockId) throw new Error("Failed to create image block");

    // Upload image
    const token2 = await getToken();
    let imageBuffer, fileName;
    if (url) {
      const res = await fetch(url);
      imageBuffer = Buffer.from(await res.arrayBuffer());
      fileName = new URL(url).pathname.split("/").pop() || "image.png";
    } else if (file_path) {
      const fs = await import("node:fs");
      imageBuffer = fs.readFileSync(file_path);
      fileName = path.basename(file_path);
    } else {
      throw new Error("Provide --url or --file_path");
    }

    // Upload via media API
    const formData = new FormData();
    formData.append("file_name", fileName);
    formData.append("parent_type", "docx_image");
    formData.append("parent_node", imageBlockId);
    formData.append("size", String(imageBuffer.length));
    formData.append("file", new Blob([imageBuffer]), fileName);

    const uploadRes = await fetch(`${BASE_URL}/drive/v1/medias/upload_all`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token2}` },
      body: formData,
    });
    const uploadData = await uploadRes.json();
    if (uploadData.code !== 0) throw new Error(`Image upload failed: ${uploadData.msg}`);
    const fileToken = uploadData.data.file_token;

    // Replace image in block
    await api("PATCH", `/docx/v1/documents/${doc_token}/blocks/${imageBlockId}`, {
      body: { replace_image: { token: fileToken } },
    });
    return { success: true, block_id: imageBlockId, file_token: fileToken };
  },

  async upload_file({ doc_token, url, file_path, filename }) {
    const token2 = await getToken();
    let fileBuffer, fileName;
    if (url) {
      const res = await fetch(url);
      fileBuffer = Buffer.from(await res.arrayBuffer());
      fileName = filename || new URL(url).pathname.split("/").pop() || "file";
    } else if (file_path) {
      const fs = await import("node:fs");
      fileBuffer = fs.readFileSync(file_path);
      fileName = filename || path.basename(file_path);
    } else {
      throw new Error("Provide --url or --file_path");
    }

    const formData = new FormData();
    formData.append("file_name", fileName);
    formData.append("parent_type", "docx_file");
    formData.append("parent_node", doc_token);
    formData.append("size", String(fileBuffer.length));
    formData.append("file", new Blob([fileBuffer]), fileName);

    const uploadRes = await fetch(`${BASE_URL}/drive/v1/medias/upload_all`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token2}` },
      body: formData,
    });
    const uploadData = await uploadRes.json();
    if (uploadData.code !== 0) throw new Error(`File upload failed: ${uploadData.msg}`);
    return { success: true, file_token: uploadData.data.file_token, file_name: fileName };
  },

  async insert({ doc_token, content, after_block_id }) {
    const blockInfo = await api("GET", `/docx/v1/documents/${doc_token}/blocks/${after_block_id}`);
    const parentId = blockInfo.block?.parent_id ?? doc_token;
    const children = await api("GET", `/docx/v1/documents/${doc_token}/blocks/${parentId}/children`);
    const index = (children.items ?? []).findIndex((b) => b.block_id === after_block_id);
    if (index === -1) throw new Error(`after_block_id "${after_block_id}" not found`);

    const converted = await api("POST", "/docx/v1/documents/convert", {
      body: { content_type: "markdown", content },
    });
    if (converted.blocks?.length > 0) {
      await api("POST", `/docx/v1/documents/${doc_token}/blocks/${parentId}/children`, {
        body: {
          children: converted.blocks,
          children_id: converted.first_level_block_ids,
          index: index + 1,
        },
      });
    }
    return { success: true, blocks_added: converted.blocks?.length ?? 0 };
  },
};

// --- Drive ---
const drive = {
  async list({ folder_token }) {
    const params = folder_token ? { folder_token } : {};
    const data = await api("GET", "/drive/v1/files", { params });
    return { files: data.files ?? [] };
  },

  async info({ file_token, type }) {
    const data = await api("GET", `/drive/v1/metas/${file_token}`, {
      params: { type: type || "file" },
    });
    return data;
  },

  async create_folder({ name, folder_token }) {
    const data = await api("POST", "/drive/v1/files/create_folder", {
      body: { name, ...(folder_token ? { folder_token } : {}) },
    });
    return data;
  },

  async move({ file_token, type, folder_token }) {
    const data = await api("POST", `/drive/v1/files/${file_token}/move`, {
      body: { type: type || "file", folder_token },
    });
    return data;
  },

  async delete({ file_token, type }) {
    const data = await api("DELETE", `/drive/v1/files/${file_token}`, {
      params: { type: type || "file" },
    });
    return { success: true };
  },
};

// --- Perm ---
const perm = {
  async list({ token, type }) {
    const data = await api("GET", `/drive/v1/permissions/${token}/members`, {
      params: { type: type || "docx" },
    });
    return { members: data.items ?? [] };
  },

  async add({ token, type, member_type, member_id, perm: permLevel }) {
    await api("POST", `/drive/v1/permissions/${token}/members`, {
      params: { type: type || "docx", need_notification: false },
      body: { member_type, member_id, perm: permLevel },
    });
    return { success: true, member_type, member_id, perm: permLevel };
  },

  async remove({ token, type, member_type, member_id }) {
    await api("DELETE", `/drive/v1/permissions/${token}/members/${member_id}`, {
      params: { type: type || "docx", member_type },
    });
    return { success: true };
  },
};

// --- Wiki ---
const wiki = {
  async spaces() {
    const data = await api("GET", "/wiki/v2/spaces", { params: { page_size: 50 } });
    return { spaces: (data.items ?? []).map((s) => ({ space_id: s.space_id, name: s.name })) };
  },

  async nodes({ space_id, parent_node_token }) {
    const data = await api("GET", `/wiki/v2/spaces/${space_id}/nodes`, {
      params: { parent_node_token, page_size: 50 },
    });
    return { nodes: (data.items ?? []).map((n) => ({
      node_token: n.node_token, obj_token: n.obj_token, obj_type: n.obj_type, title: n.title,
    }))};
  },

  async get({ token }) {
    const data = await api("GET", "/wiki/v2/spaces/get_node", { params: { token } });
    const n = data.node;
    return {
      node_token: n?.node_token, space_id: n?.space_id, obj_token: n?.obj_token,
      obj_type: n?.obj_type, title: n?.title, parent_node_token: n?.parent_node_token,
    };
  },

  async create({ space_id, title, obj_type, parent_node_token }) {
    const data = await api("POST", `/wiki/v2/spaces/${space_id}/nodes`, {
      body: { obj_type: obj_type || "docx", node_type: "origin", title, parent_node_token },
    });
    return { node_token: data.node?.node_token, obj_token: data.node?.obj_token, title: data.node?.title };
  },

  async move({ space_id, node_token, target_space_id, target_parent_token }) {
    await api("POST", `/wiki/v2/spaces/${space_id}/nodes/${node_token}/move`, {
      body: { target_space_id: target_space_id || space_id, target_parent_token },
    });
    return { success: true };
  },

  async rename({ space_id, node_token, title }) {
    await api("PUT", `/wiki/v2/spaces/${space_id}/nodes/${node_token}/title`, { body: { title } });
    return { success: true, title };
  },
};

// --- Bitable ---
const bitable = {
  async get_meta({ url }) {
    const u = new URL(url);
    const tableId = u.searchParams.get("table") ?? undefined;
    const baseMatch = u.pathname.match(/\/(base|wiki)\/([A-Za-z0-9]+)/);
    if (!baseMatch) throw new Error("Invalid URL. Expected /base/XXX or /wiki/XXX");
    const token = baseMatch[2];
    const isWiki = baseMatch[1] === "wiki";

    let appToken = token;
    if (isWiki) {
      const node = await api("GET", "/wiki/v2/spaces/get_node", { params: { token } });
      if (node.node?.obj_type !== "bitable") throw new Error("Node is not a bitable");
      appToken = node.node.obj_token;
    }

    const app = await api("GET", `/bitable/v1/apps/${appToken}`);
    let tables;
    if (!tableId) {
      const tbl = await api("GET", `/bitable/v1/apps/${appToken}/tables`);
      tables = (tbl.items ?? []).map((t) => ({ table_id: t.table_id, name: t.name }));
    }
    return { app_token: appToken, table_id: tableId, name: app.app?.name, tables };
  },

  async list_fields({ app_token, table_id }) {
    const data = await api("GET", `/bitable/v1/apps/${app_token}/tables/${table_id}/fields`);
    return { fields: (data.items ?? []).map((f) => ({
      field_id: f.field_id, field_name: f.field_name, type: f.type, is_primary: f.is_primary,
    }))};
  },

  async list_records({ app_token, table_id, page_size, page_token }) {
    const data = await api("GET", `/bitable/v1/apps/${app_token}/tables/${table_id}/records`, {
      params: { page_size: page_size || 100, page_token },
    });
    return { records: data.items ?? [], has_more: data.has_more, page_token: data.page_token };
  },

  async get_record({ app_token, table_id, record_id }) {
    const data = await api("GET", `/bitable/v1/apps/${app_token}/tables/${table_id}/records/${record_id}`);
    return { record: data.record };
  },

  async create_record({ app_token, table_id, fields }) {
    const data = await api("POST", `/bitable/v1/apps/${app_token}/tables/${table_id}/records`, {
      body: { fields },
    });
    return { record: data.record };
  },

  async update_record({ app_token, table_id, record_id, fields }) {
    const data = await api("PUT", `/bitable/v1/apps/${app_token}/tables/${table_id}/records/${record_id}`, {
      body: { fields },
    });
    return { record: data.record };
  },

  async create_app({ name, folder_token }) {
    const data = await api("POST", "/bitable/v1/apps", {
      body: { name, ...(folder_token ? { folder_token } : {}) },
    });
    return { app_token: data.app?.app_token, name: data.app?.name, url: data.app?.url };
  },

  async create_field({ app_token, table_id, field_name, field_type, property }) {
    const data = await api("POST", `/bitable/v1/apps/${app_token}/tables/${table_id}/fields`, {
      body: { field_name, type: field_type, ...(property ? { property } : {}) },
    });
    return { field_id: data.field?.field_id, field_name: data.field?.field_name, type: data.field?.type };
  },
};

// --- Main ---
const tools = { doc, drive, perm, wiki, bitable };

async function main() {
  const [tool, action, ...rest] = process.argv.slice(2);
  if (!tool || !action || tool === "--help" || tool === "-h") {
    console.log(`Usage: feishu.mjs <tool> <action> [--param value ...]

Tools: doc, drive, perm, wiki, bitable
Run: node feishu.mjs <tool> <action> --help (for specific tool help)

Examples:
  feishu.mjs doc read --doc_token ABC123
  feishu.mjs drive list --folder_token fldcnXXX
  feishu.mjs wiki spaces`);
    process.exit(tool === "--help" || tool === "-h" ? 0 : 2);
  }

  const toolFn = tools[tool];
  if (!toolFn) { console.error(`Unknown tool: ${tool}. Available: ${Object.keys(tools).join(", ")}`); process.exit(1); }

  const actionFn = toolFn[action];
  if (!actionFn) { console.error(`Unknown action: ${tool} ${action}. Available: ${Object.keys(toolFn).join(", ")}`); process.exit(1); }

  const params = parseArgs(rest);
  try {
    const result = await actionFn(params);
    console.log(JSON.stringify(result, null, 2));
  } catch (err) {
    console.error(JSON.stringify({ error: err.message }, null, 2));
    process.exit(1);
  }
}

main();
