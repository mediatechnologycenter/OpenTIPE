# Copyright 2022 ETH Zurich, Media Technology Center
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import json
from enum import Enum
from http import HTTPStatus
from typing import List, Dict, Optional, Set

from fastapi import HTTPException
from firebase_admin.auth import UserRecord
from pydantic import BaseModel, Field


class AuthenticationRole(Enum):
    value: str

    admin = "admin"
    viewer = "viewer"

    @staticmethod
    def special_roles_with_access_privileges() -> Set[str]:
        return {AuthenticationRole.admin.name, AuthenticationRole.viewer.name}


class ApiType(BaseModel):
    class Config:
        allow_population_by_field_name = True

    @property
    def json_dict(self) -> Dict:
        """
        Returns a dict that is equivalent to the JSON serialized
        """
        return json.loads(self.json(by_alias=True, exclude_none=True))


class StandardTags(Enum):
    value: str

    demo = "demo"
    dashboard = "dashboard"


class ApiStatus(ApiType):
    readiness: bool = Field(description="True if the api is ready to receive requests")
    gpu_supported: bool = Field(description="True if the api can be accelerated using a GPU")
    gpu_enabled: bool = Field(description="True if the api currently has access to a GPU where it is deployed")
    tags: List[str] = Field(
        default=[StandardTags.demo.value],
        description="A List of tags that can be used to determine attributes of the api. Defaults to ['demo'], which indicates the api is part of a project demo"
    )


class ApiRoute(ApiType):
    name: str
    path: str
    tags: List[str]


class FirebaseUser(ApiType):
    email: str = Field(example="mail@inf.ethz.ch", description="The user email. This is also used as the user ID")
    roles: List[str] = Field(example=["admin", "test"], description="The Firebase roles which grant access to certain projects or admin tools")
    access_token: Optional[str] = Field(default=None, description="The users firebase token. This token is required to access any authenticated API route")
    password: Optional[str] = Field(default=None, example="someSecurePW", description="User password. This is only ever used in order to create a new user")

    @staticmethod
    def from_user_record(user: UserRecord) -> FirebaseUser:
        try:
            roles = list(user.custom_claims.keys())
        except AttributeError:
            roles = []

        return FirebaseUser(
            email=user.email,
            roles=roles,
        )

    @staticmethod
    def default() -> FirebaseUser:
        return FirebaseUser(
            email="default@mtc.ch",
            roles=[],
        )

    @staticmethod
    def example() -> FirebaseUser:
        return FirebaseUser(
            email="test@test.ch",
            roles=[AuthenticationRole.viewer.value],
        )

    @staticmethod
    def check_authentication(user: FirebaseUser, project_name: str, include_special_rules: bool = True) -> None:
        """
        Compares the users roles with the project's name in order to determine if the user has permission on said project.
        Throws HTTPException if the user does not have permission to access.
        """

        authenticated_roles = {project_name}
        if include_special_rules:
            authenticated_roles = authenticated_roles.union(AuthenticationRole.special_roles_with_access_privileges())

        if not authenticated_roles.intersection(set(user.roles)):
            raise HTTPException(
                detail=f"Unauthorized: User does not have any of the required roles: {authenticated_roles}",
                status_code=HTTPStatus.FORBIDDEN
            )


class FirebaseUserList(ApiType):
    users: List[FirebaseUser]
