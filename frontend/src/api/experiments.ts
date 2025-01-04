import axios from "axios";

export const getExperiments = async () => {
  const response = await axios.get("/api/experiments");
  return response.data;
};

export const createExperiment = async (experiment: any) => {
  const response = await axios.post("/api/experiments", experiment);
  return response.data;
};
