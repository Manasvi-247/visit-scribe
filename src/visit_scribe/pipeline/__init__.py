from visit_scribe.pipeline.base import Pipeline, PipelineOutput
from visit_scribe.pipeline.baseline import BaselinePipeline

PIPELINES: dict[str, type[Pipeline]] = {
    BaselinePipeline.name: BaselinePipeline,
}

__all__ = ["PIPELINES", "Pipeline", "PipelineOutput"]
