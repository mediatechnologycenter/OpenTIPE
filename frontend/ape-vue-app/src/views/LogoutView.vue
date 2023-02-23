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
      <div v-if="loggedOut" class="flex flex-col">
        <h1 class="mx-auto text-xl font-heading mb-8">
          Successfully logged out.
        </h1>
        <base-button
          title="Log in again"
          type="primary-green"
          @click="buttonClicked"
        ></base-button>
      </div>
      <div v-else>
        <h1 class="mx-auto text-xl font-heading">Logging you out...</h1>
      </div>
    </base-card>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue';
import { getAuth, signOut } from 'firebase/auth';
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
  setup() {
    const auth = getAuth();
    const loggedOut = ref(false);
    const router = useRouter();
    const notifier = useNotifier();

    signOut(auth)
      .then(() => {
        loggedOut.value = true;
      })
      .catch(() => {
        notifier.notify(
          'Something went wrong. Please reload the page to try again.',
          {
            messageType: NotificationMessageType.error,
          },
        );
      });

    function buttonClicked() {
      router.push({
        name: 'AuthenticationView',
      });
    }

    return {
      loggedOut,
      buttonClicked,
    };
  },
});
</script>
