import axios from "axios";

export const getTestCases = async () => {
  const response = await axios.get("/api/test-cases");
  return response.data;
};
