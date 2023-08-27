from functools import cached_property
from pathlib import Path
from typing import Any

import jproperties  # pyright: ignore[reportMissingTypeStubs]
from hatchling.bridge.app import Application
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from pydantic import BaseModel, Field

from hatch_gradle_version.gradle import GradleVersion, load_properties


class GradleDependency(BaseModel):
    package: str
    op: str
    key: str
    py_version: str = Field(alias="py-version")
    suffix: str = ""

    def version_specifier(self, p: jproperties.Properties, app: Application):
        gradle = self.gradle_version(p)

        full_version = gradle.full_version(self.py_version, self.suffix)
        lower_bound = self.op + full_version

        if not gradle.rc:
            return self.package + lower_bound

        if "<" not in self.op:
            app.display_warning(
                f"WARNING: Dependency on package {self.package} will ONLY accept {full_version} (because gradle_version {self.gradle_version} is a prerelease)."
            )

        upper_bound = "<" + gradle.next_full_rc_version(self.py_version, self.suffix)
        return f"{self.package}{lower_bound},{upper_bound}"

    def gradle_version(self, p: jproperties.Properties):
        return GradleVersion.from_properties(p, self.key)


class GradlePropertiesBuildHookConfig(BaseModel):
    path: Path = Path("gradle.properties")
    gradle_dependencies: list[GradleDependency] = Field(alias="gradle-dependencies")


class GradlePropertiesBuildHook(BuildHookInterface[Any]):
    PLUGIN_NAME = "gradle-properties"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        build_data.setdefault("dependencies", [])

        p = load_properties(self.path)
        for dependency in self.gradle_dependencies:
            build_data["dependencies"].append(dependency.version_specifier(p, self.app))

    @cached_property
    def typed_config(self):
        return GradlePropertiesBuildHookConfig.model_validate(self.config)

    @property
    def path(self):
        return self.typed_config.path

    @property
    def gradle_dependencies(self):
        return self.typed_config.gradle_dependencies