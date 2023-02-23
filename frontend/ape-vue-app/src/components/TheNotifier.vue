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
  <base-notification
    :show="showNotification"
    :messageType="notificationType"
    :message="notificationMessage"
    @dismiss="notifier?.dismissCurrentNotification()"
  >
  </base-notification>
  <div class="inset-0 fixed pointer-events-none" style="z-index: 200000"></div>
</template>

<script lang="ts">
import { defineComponent, PropType, ref } from 'vue';
import { NotificationMessageType } from '@/modules/types';
import BaseNotification from './UI/BaseNotification.vue';
import { Notifier } from '@/modules/Notifier';

export default defineComponent({
  components: {
    BaseNotification,
  },
  props: {
    notifier: {
      type: Object as PropType<Notifier>,
      required: true,
    },
  },
  setup(props) {
    const showNotification = ref(false);
    const notificationType = ref(NotificationMessageType.alert);
    const notificationMessage = ref('');

    if (!props.notifier) {
      throw new Error('Notifier is undefined.');
    }

    props.notifier.onNewNotification((msg, options) => {
      notificationMessage.value = msg;
      showNotification.value = true;
      notificationType.value = options.messageType;
    });

    props.notifier.onDismissNotification(() => {
      showNotification.value = false;
    });

    return {
      showNotification,
      notificationType,
      notificationMessage,
    };
  },
});
</script>
