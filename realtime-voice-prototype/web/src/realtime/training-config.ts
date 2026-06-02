export interface TrainingConfig {
  jobId: string;
  modeId: string;
  competencyId: string;
  strategyId: string;
}

export const DEFAULT_TRAINING_CONFIG: TrainingConfig = {
  jobId: "product_manager",
  modeId: "standard",
  competencyId: "requirement_analysis",
  strategyId: "evidence_probe",
};

export const TRAINING_OPTIONS = {
  jobs: [{ id: "product_manager", label: "\u4ea7\u54c1\u7ecf\u7406" }],
  modes: [
    { id: "standard", label: "\u6807\u51c6\u8bad\u7ec3" },
    { id: "guided", label: "\u5f15\u5bfc\u8bad\u7ec3" },
    { id: "challenge", label: "\u538b\u529b\u8ffd\u95ee" },
  ],
  competencies: [
    { id: "requirement_analysis", label: "\u9700\u6c42\u5206\u6790" },
    { id: "project_delivery", label: "\u9879\u76ee\u63a8\u8fdb" },
    { id: "impact_expression", label: "\u7ed3\u679c\u8868\u8fbe" },
  ],
  strategies: [
    { id: "clarification_probe", label: "\u6f84\u6e05\u8ffd\u95ee" },
    { id: "evidence_probe", label: "\u8bc1\u636e\u8ffd\u95ee" },
    { id: "result_probe", label: "\u7ed3\u679c\u8ffd\u95ee" },
    { id: "reflection_probe", label: "\u590d\u76d8\u8ffd\u95ee" },
  ],
} as const;
