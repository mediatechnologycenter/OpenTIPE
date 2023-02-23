// Copyright 2022 ETH Zurich, Media Technology Center

// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at

//   http://www.apache.org/licenses/LICENSE-2.0

// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
import {
  createRouter,
  createWebHistory,
  RouteParamsRaw,
  RouteRecordRaw,
} from 'vue-router';
import { watchEffect } from 'vue';
import StartView from '../views/StartView.vue';
import SuggestionsView from '../views/SuggestionsView.vue';
import AuthenticationView from '@/views/AuthenticationView.vue';
import LogoutView from '@/views/LogoutView.vue';
import PageNotFoundView from '@/views/PageNotFoundView.vue';
import { authenticationIsEnabled } from '@/modules/otherUtil';

interface GetRouterOptions {
  store: any;
}

interface RouteMeta {
  // Page can only be visited when logged in
  requiresAuth?: boolean;
  // Page can only be visited when logged out
  requiresNoAuth?: boolean;
  // The page has no other function than authentication
  authRelated?: boolean;
  // By default, if the auth status changes, the user will be redirected to a different page
  // if they are not allowed to see the current one. This behavior can be disabled here.
  preventRedirectOnAuthStateChange?: boolean;
}

function getRouter({ store }: GetRouterOptions) {
  const { state } = store;

  const routes = [
    // Home
    {
      path: '/',
      name: 'StartView',
      component: StartView,
      meta: {
        requiresAuth: true,
      },
    },

    // Suggestions
    {
      path: '/suggestions',
      name: 'SuggestionsView',
      component: SuggestionsView,
      meta: {
        requiresAuth: true,
      } as RouteMeta,
      beforeEnter: (_to, _from, next) => {
        // Check if translation data is available.
        // If not, go to the first screen.
        if (state.textSegmentsFromApi) {
          next();
        } else {
          next({ name: 'StartView' });
        }
      },
    },

    // Sign-in page
    {
      path: '/auth',
      name: 'AuthenticationView',
      component: AuthenticationView,
      props: true,
      meta: {
        // Visiting this page is pointless if the user is already authenticated.
        requiresNoAuth: true,
        authRelated: true,
      } as RouteMeta,
    },

    // Logout page
    {
      path: '/logout',
      name: 'LogoutView',
      component: LogoutView,
      meta: {
        // Visiting this page is pointless if the user is not authenticated.
        requiresAuth: true,
        // Better UX if the user isn't immediately redirected to a different page once the logout
        // is complete.
        preventRedirectOnAuthStateChange: true,
        authRelated: true,
      } as RouteMeta,
    },

    // Page not found
    {
      path: '/:catchAll(.*)',
      name: 'PageNotFoundView',
      component: PageNotFoundView,
    },
  ] as RouteRecordRaw[];

  const router = createRouter({
    history: createWebHistory(),
    routes,
  });

  // Reacting to authentication state changes
  watchEffect(() => {
    // eslint-disable-next-line prefer-destructuring
    const meta: RouteMeta = router.currentRoute.value.meta;
    const currentPath = router.currentRoute.value.fullPath;

    if (!authenticationIsEnabled() || meta.preventRedirectOnAuthStateChange) {
      return;
    }

    if (!state.user && meta.requiresAuth) {
      // Move user to auth page if user is on a protected page and becomes unauthorized.
      router.push({
        name: 'AuthenticationView',
        params: {
          targetPath: currentPath,
        },
      });
    } else if (state.user && meta.requiresNoAuth) {
      // Move user to homepage if they are on a page that requires to be unauthenticated
      // and they become authenticated.
      router.push({
        name: 'StartView',
        params: {
          targetPath: currentPath,
        },
      });
    }
  });

  router.beforeEach((to, from, next) => {
    // eslint-disable-next-line prefer-destructuring
    const toMeta: RouteMeta = to.meta;

    // Disable pages like '/auth' and '/logout' if authentication is disabled.
    if (!authenticationIsEnabled() && toMeta.authRelated) {
      next(from);
      return;
    }

    if (!authenticationIsEnabled()) {
      next();
      return;
    }

    // Redirect user to auth page if they are not logged in and page is protected.
    if (toMeta.requiresAuth && !state.user) {
      const params: RouteParamsRaw = {};

      // Prevents that the sign in page will redirect to the logout page after successful authentication
      if (to.name !== 'LogoutView') {
        params.targetPath = to.fullPath;
      }

      next({
        name: 'AuthenticationView',
        params,
      });
      return;
    }

    // Prevent going to a page that requires to be unauthenticated if the user is authenticated.
    if (toMeta.requiresNoAuth && state.user) {
      next(from);
      return;
    }

    // No redirection, just follow the given route.
    next();
  });

  return router;
}

export default getRouter;
