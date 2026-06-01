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
  jobs: [{ id: "product_manager", label: "产品经理" }],
  modes: [
    { id: "standard", label: "标准训练" },
    { id: "guided", label: "引导训练" },
    { id: "challenge", label: "压力追问" },
  ],
  competencies: [
    { id: "requirement_analysis", label: "需求分析" },
    { id: "project_delivery", label: "项目推进" },
    { id: "impact_expression", label: "结果表达" },
  ],
  strategies: [
    { id: "clarification_probe", label: "澄清追问" },
    { id: "evidence_probe", label: "证据追问" },
    { id: "result_probe", label: "结果追问" },
    { id: "reflection_probe", label: "复盘追问" },
  ],
} as const;
