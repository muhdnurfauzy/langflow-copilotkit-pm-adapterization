import { CopilotKit } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

export default function App() {
  return (
    <CopilotKit runtimeUrl="http://127.0.0.1:8000/copilotkit">
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          backgroundColor: "#f4f6f8",
          fontFamily: "system-ui, sans-serif",
        }}
      >
        <header style={{ marginBottom: "16px", textAlign: "center" }}>
          <h2 style={{ margin: "0 0 4px 0", color: "#111827" }}>
            Langflow + Ollama Copilot
          </h2>
          <p style={{ margin: 0, fontSize: "0.85rem", color: "#6b7280" }}>
            Model: <code>openai/gpt-oss-20b</code>
          </p>
        </header>

        <div
          style={{
            width: "440px",
            height: "600px",
            borderRadius: "12px",
            boxShadow: "0 10px 25px rgba(0,0,0,0.1)",
            overflow: "hidden",
            backgroundColor: "#fff",
          }}
        >
          <CopilotChat
            labels={{
              title: "Ollama Assistant",
              initial: "Hi! I am connected to your Langflow flow. Ask me anything!",
            }}
          />
        </div>
      </div>
    </CopilotKit>
  );
}