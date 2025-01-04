import React, { useState } from "react";
import { createExperiment } from "../api/experiments";

const ExperimentForm: React.FC = () => {
  const [name, setName] = useState("");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [llmModel, setLlmModel] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await createExperiment({ name, systemPrompt, llmModel });
    alert("Experiment created!");
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Experiment Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
      />
      <textarea
        placeholder="System Prompt"
        value={systemPrompt}
        onChange={(e) => setSystemPrompt(e.target.value)}
      />
      <input
        type="text"
        placeholder="LLM Model"
        value={llmModel}
        onChange={(e) => setLlmModel(e.target.value)}
      />
      <button type="submit">Create Experiment</button>
    </form>
  );
};

export default ExperimentForm;
