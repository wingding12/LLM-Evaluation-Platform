import React from "react";
import ExperimentForm from "../components/ExperimentForm";

const ExperimentPage: React.FC = () => {
  return (
    <div>
      <h1>Create a New Experiment</h1>
      <ExperimentForm />
    </div>
  );
};

export default ExperimentPage;
