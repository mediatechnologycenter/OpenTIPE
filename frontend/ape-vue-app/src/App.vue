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
  <the-notifier :notifier="notifier"></the-notifier>

  <router-view v-slot="{ Component, route }">
    <transition name="fade-route">
      <!-- Transition takes only one child. Therefore, we must wrap the components. -->
      <!-- The transition will trigger when key updates -->
      <!-- This div also applies the background to any view -->
      <div
        :key="route.name"
        class="bg-gradient-to-bl from-gray-100 to-gray-200 fixed inset-0 overflow-auto"
      >
        <!-- This is replaced by the componentes specified in the router -->
        <component :is="Component"></component>
      </div>
    </transition>
  </router-view>
</template>

<script lang='ts'>
import { defineComponent } from 'vue';
import TheNotifier from './components/TheNotifier.vue';
import { useNotifier } from './modules/injectUtil';

export default defineComponent({
  components: {
    TheNotifier,
  },
  setup() {
    return {
      notifier: useNotifier(),
    };
  },
});
</script>

<style scoped>
.fade-route-enter-active,
.fade-route-leave-active {
  @apply transition-opacity;
}

.fade-route-enter-from,
.fade-route-leave-to {
  @apply opacity-0;
}
</style>
