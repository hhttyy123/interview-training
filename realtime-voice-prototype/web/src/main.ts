import { VoicePrototypeApp } from "./app";
import "./styles.css";

const root = document.querySelector<HTMLDivElement>("#app");

if (!root) {
  throw new Error("Application root was not found.");
}

new VoicePrototypeApp(root).render();
