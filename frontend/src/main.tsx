import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import { getOrCreateSessionId } from "./lib/session";
import "./index.css";

getOrCreateSessionId();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
