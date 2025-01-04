import React, { useEffect, useState } from "react";
import { getExperiments } from "../api/experiments";

const ExperimentDashboard: React.FC = () => {
  const [experiments, setExperiments] = useState([]);

  useEffect(() => {
    const fetchExperiments = async () => {
      const data = await getExperiments();
      setExperiments(data);
    };
    fetchExperiments();
  }, []);

  return (
    <div>
      <h1>Experiment Dashboard</h1>
      <ul>
        {experiments.map((experiment: any) => (
          <li key={experiment.id}>{experiment.name}</li>
        ))}
      </ul>
    </div>
  );
};

export default ExperimentDashboard;
