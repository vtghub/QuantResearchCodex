from datetime import UTC, datetime
from uuid import uuid4

from quantresearch_api.schemas import (
    ArtifactVersion,
    CreateArtifactVersionRequest,
    CreateDatasetManifestRequest,
    DatasetStorageManifest,
    TenantContext,
)


class CatalogService:
    def __init__(self) -> None:
        self._datasets: dict[str, DatasetStorageManifest] = {}
        self._artifacts: dict[str, ArtifactVersion] = {}

    def create_dataset(
        self,
        request: CreateDatasetManifestRequest,
        context: TenantContext,
    ) -> DatasetStorageManifest:
        manifest = DatasetStorageManifest(
            id=f"dataset-{uuid4()}",
            tenant_id=context.tenant_id,
            workspace_id=context.workspace_id,
            provider=request.provider,
            symbols=request.symbols,
            asset_class=request.asset_class,
            storage_uri=request.storage_uri,
            storage_format=request.storage_format,
            checksum=request.checksum,
            row_count=request.row_count,
            entitlement=request.entitlement,
            transform_version=request.transform_version,
            created_at=datetime.now(UTC),
        )
        self._datasets[manifest.id] = manifest
        return manifest

    def datasets(self, context: TenantContext) -> list[DatasetStorageManifest]:
        return [
            dataset
            for dataset in self._datasets.values()
            if dataset.tenant_id == context.tenant_id
            and dataset.workspace_id == context.workspace_id
        ]

    def create_artifact(
        self,
        request: CreateArtifactVersionRequest,
        context: TenantContext,
    ) -> ArtifactVersion:
        version = ArtifactVersion(
            id=f"artifact-{uuid4()}",
            tenant_id=context.tenant_id,
            workspace_id=context.workspace_id,
            artifact_type=request.artifact_type,
            name=request.name,
            version=request.version,
            source_run_id=request.source_run_id,
            storage_uri=request.storage_uri,
            checksum=request.checksum,
            metrics=request.metrics,
            created_at=datetime.now(UTC),
        )
        self._artifacts[version.id] = version
        return version

    def artifacts(self, context: TenantContext) -> list[ArtifactVersion]:
        return [
            artifact
            for artifact in self._artifacts.values()
            if artifact.tenant_id == context.tenant_id
            and artifact.workspace_id == context.workspace_id
        ]


catalog_service = CatalogService()
