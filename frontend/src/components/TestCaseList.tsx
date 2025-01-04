import React, { useEffect, useState } from "react";
import { getTestCases } from "../api/testCases";

const TestCaseList: React.FC = () => {
  const [testCases, setTestCases] = useState([]);

  useEffect(() => {
    const fetchTestCases = async () => {
      const data = await getTestCases();
      setTestCases(data);
    };
    fetchTestCases();
  }, []);

  return (
    <ul>
      {testCases.map((testCase: any) => (
        <li key={testCase.id}>{testCase.name}</li>
      ))}
    </ul>
  );
};

export default TestCaseList;
