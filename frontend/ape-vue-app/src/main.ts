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
import { createApp } from 'vue';
import { initializeApp } from 'firebase/app';
import { getAuth, setPersistence } from '@firebase/auth';
import App from './App.vue';
import getRouter from './router';
import './styles/index.css';
import { storeKey, store } from './store/index';
import options from './modules/options';
import { Notifier, notifierKey } from './modules/Notifier';
import { authenticationIsEnabled } from './modules/otherUtil';

if (authenticationIsEnabled()) {
  initializeApp(options.firebaseConfig);
  const auth = getAuth();
  setPersistence(auth, options.loginPersistence);
  // Update user in application store whenever the auth state changes
  auth.onAuthStateChanged((user) => {
    store.methods.updateState({
      user,
    });
  });
}
// Firebase authentication

const app = createApp(App);

// Make the store and the notifier accessible from everywhere
app.provide(storeKey, store);
app.provide(notifierKey, new Notifier());

app.use(getRouter({ store }));

// Connect Vue app to DOM
app.mount('#app');
