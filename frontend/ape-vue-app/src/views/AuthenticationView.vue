<!-- Copyright 2022 ETH Zurich, Media Technology Center

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. -->
<template>
  <div class="flex justify-center items-center h-full">
    <base-card class="p-8 w-full max-w-md">
      <form class="flex flex-col space-y-4" @submit.prevent="buttonClicked">
        <h1 class="font-heading text-lg pb-2">Sign In</h1>
        <input
          v-model="email"
          ref="emailInput"
          class="
            appearance-none
            border
            rounded
            w-full
            py-2
            px-3
            text-gray-700
            leading-tight
            outline-none
            focus:ring
            ring-blue-200
          "
          id="email"
          type="email"
          placeholder="E-mail"
          required
        />
        <input
          v-model="password"
          ref="passwordInput"
          class="
            appearance-none
            border
            rounded
            w-full
            py-2
            px-3
            text-gray-700
            leading-tight
            outline-none
            focus:ring
            ring-blue-200
          "
          id="password"
          type="password"
          placeholder="Password"
          required
        />
        <base-button
          title="Log in"
          type="primary-green"
          class="pt-4"
          :disabled="!buttonIsEnabled"
        ></base-button>
      </form>
    </base-card>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, watch } from 'vue';
import { getAuth, signInWithEmailAndPassword } from 'firebase/auth';
import { useRouter } from 'vue-router';
import BaseCard from '@/components/UI/BaseCard.vue';
import BaseButton from '@/components/UI/BaseButton.vue';
import { NotificationMessageType } from '@/modules/types';
import { useNotifier } from '@/modules/injectUtil';

export default defineComponent({
  components: {
    BaseCard,
    BaseButton,
  },
  props: {
    targetPath: {
      type: String,
      required: false,
    },
  },
  setup(props) {
    const email = ref('');
    const emailInput = ref<any>(null);
    const password = ref('');
    const passwordInput = ref<any>(null);
    const buttonIsEnabled = ref(false);
    const auth = getAuth();
    const router = useRouter();

    const notifier = useNotifier();

    watch([email, password], () => {
      if (
        emailInput.value.checkValidity()
        && passwordInput.value.checkValidity()
      ) {
        buttonIsEnabled.value = true;
      } else {
        buttonIsEnabled.value = false;
      }
    });

    function buttonClicked() {
      signInWithEmailAndPassword(auth, email.value, password.value)
        .then(() => {
          // A authentication state change listener adds the user to the global app state.
          // See main.ts

          // Go to the page the user wanted to go to (if there was one). Otherwise, go home.
          const path = props.targetPath || '/';
          router.push({
            path,
          });
        })
        .catch(() => {
          notifier.notify(
            'Something is not right. Please check your input and try again.',
            {
              messageType: NotificationMessageType.alert,
            },
          );
        });
    }

    return {
      email,
      password,
      emailInput,
      passwordInput,
      buttonIsEnabled,
      buttonClicked,
    };
  },
});
</script>
