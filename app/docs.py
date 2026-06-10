"""本地 API 文档页面。

FastAPI 默认的 `/docs` 使用 Swagger UI，页面里的 JS/CSS 来自外网 CDN。
在内网、公司网络、浏览器无法访问 CDN 的情况下，`/docs` 会拿到 HTML，
但是 JS 没加载成功，所以页面看起来就是空白。

这个文件提供一个“零外部依赖”的文档页面：
1. HTML、CSS、JS 都写在同一个字符串里；
2. 浏览器只需要访问当前 FastAPI 服务；
3. 页面启动后再请求 `/openapi.json`，把接口列表渲染出来；
4. 对 GET 接口提供一个简单的“调用接口”按钮，方便你学习和调试。
"""


def get_local_docs_html(openapi_url: str = "/openapi.json") -> str:
    """返回本地自包含的 HTML 文档页面。

    参数说明：
    - openapi_url：FastAPI 自动生成的 OpenAPI JSON 地址。

    数据流转：
    1. 浏览器访问 `/docs`；
    2. `app.main.local_docs()` 调用这个函数生成 HTML；
    3. 浏览器执行页面里的 JavaScript；
    4. JavaScript 请求 `/openapi.json`；
    5. JavaScript 根据 OpenAPI 的 paths 渲染接口列表；
    6. 用户点击“调用接口”后，浏览器直接请求对应的 GET 接口。
    """

    return f"""
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>inner-ai-tools API 文档</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #17202a;
      --muted: #607080;
      --line: #d9e0e7;
      --brand: #1463ff;
      --brand-dark: #0f48bd;
      --ok: #16794c;
      --warn: #9a5b00;
      --code: #111827;
    }}

    * {{
      box-sizing: border-box;
    }}

    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
      line-height: 1.6;
    }}

    header {{
      background: var(--panel);
      border-bottom: 1px solid var(--line);
      padding: 24px 32px;
    }}

    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 24px 20px 48px;
    }}

    h1 {{
      margin: 0 0 8px;
      font-size: 28px;
      font-weight: 700;
    }}

    h2 {{
      margin: 0 0 12px;
      font-size: 18px;
    }}

    p {{
      margin: 0;
      color: var(--muted);
    }}

    a {{
      color: var(--brand);
    }}

    .notice,
    .endpoint {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 16px;
    }}

    .notice strong {{
      color: var(--warn);
    }}

    .endpoint-title {{
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 8px;
      flex-wrap: wrap;
    }}

    .method {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 48px;
      height: 28px;
      border-radius: 4px;
      background: var(--ok);
      color: white;
      font-weight: 700;
      font-size: 13px;
    }}

    code {{
      color: var(--code);
      background: #eef2f7;
      border-radius: 4px;
      padding: 2px 6px;
      font-family: Consolas, "Courier New", monospace;
      overflow-wrap: anywhere;
    }}

    button {{
      height: 34px;
      border: 0;
      border-radius: 6px;
      background: var(--brand);
      color: white;
      padding: 0 12px;
      cursor: pointer;
      font-weight: 600;
    }}

    button:hover {{
      background: var(--brand-dark);
    }}

    pre {{
      display: none;
      margin: 12px 0 0;
      padding: 12px;
      background: #111827;
      color: #f9fafb;
      border-radius: 6px;
      overflow: auto;
      max-height: 360px;
      font-size: 13px;
    }}
  </style>
</head>
<body>
  <header>
    <h1>inner-ai-tools API 文档</h1>
    <p>本页面不依赖外网 CDN。Dify Tool 导入请使用 <code>{openapi_url}</code>。</p>
  </header>

  <main>
    <section class="notice">
      <h2>为什么原来的 /docs 是空白？</h2>
      <p>
        FastAPI 默认 Swagger UI 会从 <strong>cdn.jsdelivr.net</strong> 加载 JS/CSS。
        如果浏览器访问不到外网 CDN，HTML 虽然返回成功，但页面脚本没加载，所以会显示空白。
      </p>
    </section>

    <section class="notice">
      <h2>接口列表</h2>
      <p>下面的接口来自 <code>{openapi_url}</code>。点击“调用接口”会直接请求当前 FastAPI 服务。</p>
    </section>

    <section id="endpoints"></section>
  </main>

  <script>
    const openapiUrl = "{openapi_url}";
    const endpointsEl = document.querySelector("#endpoints");

    function createEndpoint(path, method, operation) {{
      const article = document.createElement("article");
      article.className = "endpoint";

      const title = document.createElement("div");
      title.className = "endpoint-title";
      title.innerHTML = `
        <span class="method">${{method.toUpperCase()}}</span>
        <code>${{path}}</code>
        <button type="button">调用接口</button>
      `;

      const summary = document.createElement("p");
      summary.textContent = operation.summary || operation.description || "无接口说明";

      const output = document.createElement("pre");

      const button = title.querySelector("button");
      button.addEventListener("click", async () => {{
        output.style.display = "block";
        output.textContent = "请求中...";
        try {{
          const response = await fetch(path);
          const text = await response.text();
          try {{
            output.textContent = JSON.stringify(JSON.parse(text), null, 2);
          }} catch (_error) {{
            output.textContent = text;
          }}
        }} catch (error) {{
          output.textContent = `请求失败：${{error}}`;
        }}
      }});

      article.append(title, summary, output);
      return article;
    }}

    async function renderDocs() {{
      try {{
        const response = await fetch(openapiUrl);
        const schema = await response.json();
        const paths = schema.paths || {{}};

        Object.entries(paths).forEach(([path, operations]) => {{
          Object.entries(operations).forEach(([method, operation]) => {{
            endpointsEl.appendChild(createEndpoint(path, method, operation));
          }});
        }});
      }} catch (error) {{
        endpointsEl.innerHTML = `
          <section class="notice">
            <h2>加载失败</h2>
            <p>无法读取 <code>${{openapiUrl}}</code>：${{error}}</p>
          </section>
        `;
      }}
    }}

    renderDocs();
  </script>
</body>
</html>
"""
