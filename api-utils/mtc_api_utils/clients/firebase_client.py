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

from abc import ABC, abstractmethod
from copy import deepcopy
from http import HTTPStatus
from typing import Iterable, Optional, List, Type

import firebase_admin
import firebase_admin.auth as firebase_auth
import requests
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin.auth import UserRecord
from firebase_admin.credentials import Certificate

from mtc_api_utils.api_types import FirebaseUser, AuthenticationRole
from mtc_api_utils.config import Config
from mtc_api_utils.init_api import download_if_not_exists


class FirebaseClient:
    def __init__(self, config: Type[Config]):
        self.enabled = config.auth_enabled

        if self.enabled and not firebase_admin._apps:
            # Init firebase credentials
            credentials_path = download_if_not_exists(
                artifact_url=config.firebase_auth_service_account_url,
                download_dir=config.service_account_dir,
                auth=config.credentials,
            )

            cred = Certificate(credentials_path)
            firebase_admin.initialize_app(cred)

    def get_user(self, email: str) -> Optional[UserRecord]:
        """
        Retrieves user from firebase service
        """
        if self.enabled:
            return firebase_auth.get_user_by_email(email=email)
        else:
            print("Firebase auth disabled -> skipping user creation")
            return None

    def list_users(self) -> firebase_auth.ListUsersPage:
        """
        Retrieves all users from firebase service
        """
        if not self.enabled:
            raise HTTPException(detail="Firebase auth disabled", status_code=HTTPStatus.UNAUTHORIZED)

        return firebase_auth.list_users()

    def create_user(self, email: str, password: str, roles: Optional[Iterable[str]] = None) -> Optional[UserRecord]:
        """
        Creates a new user using the firebase service
        """
        if self.enabled:
            user_dict = firebase_auth.create_user(email=email, password=password)

            if roles:
                firebase_auth.set_custom_user_claims(user_dict.uid, {role: True for role in roles})
            return self.get_user(email)

        else:
            print("Firebase auth disabled -> skipping user creation")
            return None

    def update_user_roles(self, uid: str, roles: Iterable[str]) -> Optional[UserRecord]:
        """
        Updates a user using the firebase service by setting the provided user roles
        """
        if self.enabled:
            firebase_auth.set_custom_user_claims(uid, {role: True for role in roles})
            return firebase_auth.get_user(uid=uid)

        else:
            print("Firebase auth disabled -> skipping user update")
            return None

    def delete_user(self, user_id: str) -> None:
        """
        Deletes a user from the firebase service
        """
        if self.enabled:
            return firebase_auth.delete_user(uid=user_id)
        else:
            print("Firebase auth disabled -> skipping user creation")

    @staticmethod
    def verify_token(access_token: str) -> FirebaseUser:
        """
        Verifies an access token against the firebase service
        """
        try:
            if access_token is None:
                raise HTTPException(detail="Parameter access_token was not passed", status_code=HTTPStatus.UNAUTHORIZED)

            user_dict = firebase_auth.verify_id_token(access_token)

            return FirebaseUser(
                email=user_dict["email"],
                access_token=access_token,
                roles=FirebaseClient.get_user_roles(user_dict)
            )

        except Exception as e:
            print(e)
            raise HTTPException(detail="Parameter access_token is not valid", status_code=HTTPStatus.UNAUTHORIZED)

    @staticmethod
    def get_user_roles(user: dict) -> List[str]:
        """
        Extracts user roles from an authentication dict.
        """
        if not user:
            print("User is None")
            return []

        try:
            return [k for k, v in user.items() if isinstance(v, bool) and v]  # filter for boolean values that are True
        except AttributeError:
            print(f"No roles found for user: {user['email']}")
            return []

    def login_user(self, email: str, password: str, firebase_project_api_key: str) -> str:
        """
        Logs in an existing user and returns its access token
        Should only be used in tests to simulate user login using a frontend
        """

        if self.enabled:
            request_body = {
                "email": email,
                "password": password,
                "returnSecureToken": True,
            }

            resp = requests.post(
                url=f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={firebase_project_api_key}",
                json=request_body,
            )

            resp.raise_for_status()
            return resp.json()["idToken"]
        else:
            print("Firebase auth disabled -> skipping user creation")
            return ""


class UserAuth(ABC):
    @abstractmethod
    def __call__(self, token: Optional[HTTPAuthorizationCredentials]) -> Optional[dict]:
        pass

    @abstractmethod
    def with_roles(self, roles: Iterable[str], include_special_rules: bool = True):
        pass

    @abstractmethod
    def admin_only(self):
        pass


def firebase_user_auth(config: Type[Config]) -> UserAuth:
    """
    UserAuth factory for FirebaseUserAuth class allowing auth to be enabled/disabled
    """
    # Only require Bearer token Authorization header if auth_enabled
    bearer = HTTPBearer() if config.auth_enabled else lambda: None

    class FirebaseUserAuth(UserAuth):
        def __init__(self, config: Type[config]):
            self.firebase_client = FirebaseClient(config=config)

            self.roles: Iterable[str] = []
            self.auth_enabled = config.auth_enabled

        def with_roles(self, roles: Iterable[str], include_special_rules: bool = True):
            roles = set(roles)

            if include_special_rules:
                roles = roles.union(AuthenticationRole.special_roles_with_access_privileges())

            client_with_roles = deepcopy(self)
            client_with_roles.roles = roles
            return client_with_roles

        def admin_only(self):
            client_with_roles = deepcopy(self)
            client_with_roles.roles = [AuthenticationRole.admin.value]

            return client_with_roles

        def __call__(self, token: Optional[HTTPAuthorizationCredentials] = Depends(bearer)) -> Optional[FirebaseUser]:  # roles: List[str],
            if not self.auth_enabled:
                # If auth is disabled, return a default user
                return FirebaseUser.default()

            user = self.firebase_client.verify_token(token.credentials)

            if not self.roles:
                return user

            for role in self.roles:
                if role in user.roles:
                    return user

            raise HTTPException(
                detail=f"Unauthorized: User does not have any of the required roles: {self.roles}",
                status_code=HTTPStatus.FORBIDDEN
            )

    return FirebaseUserAuth(config=config)
