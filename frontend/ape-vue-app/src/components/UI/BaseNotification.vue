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
  <teleport to="body">
    <transition name="fade">
      <!-- Background -->
      <div
        v-if="show"
        class="
          h-44
          w-screen
          absolute
          left-0
          top-0
          from-black from
          bg-gradient-to-b
          opacity-10
        "
        style="z-index: 200000"
      />
    </transition>

    <transition name="drop-down">
      <!-- Invisible click area (dismisses the notification) -->
      <div
        @click="$emit('dismiss')"
        v-if="show"
        class="fixed inset-0 left-0 top-0 flex justify-center items-start pt-8"
        style="z-index: 200001"
      >
        <!-- The notification -->
        <div
          class="
            bg-white
            max-w-xl
            rounded-3xl
            flex
            items-center
            p-2
            space-x-4
            pr-5
            shadow-2xl
            justify-center
          "
        >
          <!-- Icon + icon background -->
          <div
            class="rounded-full p-2"
            :class="{
              // Success
              'bg-mtc_medium_aquamarine-400 text-mtc_medium_aquamarine-900':
                messageType === NotificationMessageType.success,

              // Alert
              'bg-yellow-400 text-yellow-900':
                messageType === NotificationMessageType.alert,

              // Error
              'bg-red-400 text-red-900':
                messageType === NotificationMessageType.error,
            }"
          >
            <check-icon
              v-if="messageType === NotificationMessageType.success"
              class="w-5 h-5"
            ></check-icon>
            <exclamation-icon
              v-else-if="messageType === NotificationMessageType.alert"
              class="w-5 h-5"
            >
            </exclamation-icon>
            <x-icon v-else class="w-5 h-5"> </x-icon>
          </div>

          <!-- Notification text -->
          <h2 class="text-gray-700 font-semibold">{{ message }}</h2>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script lang="ts">
import { CheckIcon, ExclamationIcon, XIcon } from '@heroicons/vue/solid';
import { defineComponent, PropType } from 'vue';
import { NotificationMessageType } from '@/modules/types';

export default defineComponent({
  components: {
    CheckIcon,
    ExclamationIcon,
    XIcon,
  },
  emits: {
    dismiss: () => true,
  },
  props: {
    show: {
      type: Boolean,
      required: true,
    },
    messageType: {
      type: Number as PropType<NotificationMessageType>,
      default: () => NotificationMessageType.alert,
    },
    message: {
      type: String,
      required: true,
    },
  },
  setup() {
    return {
      NotificationMessageType,
    };
  },
});
</script>

<style scoped lang="scss">
.drop-down-enter-active,
.drop-down-leave-active {
  @apply transition-all duration-300 transform translate-y-0;
}
.drop-down-enter-from,
.drop-down-leave-to {
  @apply -translate-y-full;
}

.fade-enter-active,
.fade-leave-active {
  @apply transition-all duration-300;
}
.fade-enter-from,
.fade-leave-to {
  @apply opacity-0;
}
</style>
