from abc import ABC, abstractmethod
from typing import Any, Iterator

from hatchling.metadata.plugin.interface import MetadataHookInterface
from pydantic import Field

from hatch_gradle_version.common.decorators import listify
from hatch_gradle_version.common.gradle import GradleDependency
from hatch_gradle_version.common.model import GradlePath, HookModel

Dependencies = list[str | GradleDependency]


class BaseMetadataHook(HookModel, MetadataHookInterface, ABC):
    dependencies: Dependencies = Field(default_factory=dict)
    optional_dependencies: dict[str, Dependencies] = Field(default_factory=dict)
    path: GradlePath

    @abstractmethod
    def parse_gradle_dependency(self, dependency: GradleDependency) -> str:
        ...

    def update(self, metadata: dict[str, Any]) -> None:
        """Implements MetadataHookInterface."""
        self.set_dynamic(
            metadata,
            "dependencies",
            self.parse_dependencies(self.dependencies),
        )

        self.set_dynamic(
            metadata,
            "optional-dependencies",
            {
                key: self.parse_dependencies(value)
                for key, value in self.optional_dependencies.items()
            },
        )

    @listify
    def parse_dependencies(self, dependencies: Dependencies) -> Iterator[str]:
        for dependency in dependencies:
            match dependency:
                case str():
                    yield dependency
                case GradleDependency():
                    yield self.parse_gradle_dependency(dependency)

    def set_dynamic(self, metadata: dict[str, Any], key: str, value: Any):
        if key in metadata:
            raise ValueError(
                f"`{key}` may not be listed in the `project` table when using hatch-gradle-version to populate dependencies. Please use `tool.hatch.metadata.hooks.{self.PLUGIN_NAME}.{key}` instead."
            )
        if key not in metadata.get("dynamic", []):
            raise ValueError(
                f"`{key}` must be listed in `project.dynamic` when using hatch-gradle-version to populate dependencies."
            )
        metadata[key] = value