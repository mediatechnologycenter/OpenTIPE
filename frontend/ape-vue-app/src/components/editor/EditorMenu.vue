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
  <div
    class="px-4 py-1 flex justify-between items-center bg-gray-100 rounded-b-md"
    v-if="editor"
  >
    <div class="flex justify-start items-center space-x-1">
      <!-- H1 -->
      <text-menu-button
        @click="editor.chain().focus().toggleHeading({ level: 1 }).run()"
        :active="editor.isActive('heading', { level: 1 })"
      >
        <p>H1</p>
      </text-menu-button>

      <!-- H2 -->
      <text-menu-button
        @click="editor.chain().focus().toggleHeading({ level: 2 }).run()"
        :active="editor.isActive('heading', { level: 2 })"
      >
        <p>H2</p>
      </text-menu-button>

      <!-- H3 -->
      <text-menu-button
        @click="editor.chain().focus().toggleHeading({ level: 3 }).run()"
        :active="editor.isActive('heading', { level: 3 })"
      >
        <p>H3</p>
      </text-menu-button>

      <!-- Paragraph -->
      <text-menu-button
        @click="editor.chain().focus().setParagraph().run()"
        :active="editor.isActive('paragraph')"
      >
        <p>P</p>
      </text-menu-button>

      <!-- Bulleted list -->
      <text-menu-button
        @click="editor.chain().focus().toggleBulletList().run()"
        :active="editor.isActive('bulletList')"
      >
        <bulleted-list-icon></bulleted-list-icon>
      </text-menu-button>

      <!-- Ordered list -->
      <text-menu-button
        @click="editor.chain().focus().toggleOrderedList().run()"
        :active="editor.isActive('orderedList')"
      >
        <ordered-list-icon></ordered-list-icon>
      </text-menu-button>

      <!-- Blockquote -->
      <text-menu-button
        @click="editor.chain().focus().toggleBlockquote().run()"
        :active="editor.isActive('blockquote')"
      >
        <blockquote-icon></blockquote-icon>
      </text-menu-button>

      <!-- Divider -->
      <text-menu-button
        @click="editor.chain().focus().setHorizontalRule().run()"
      >
        <p>—</p>
      </text-menu-button>
    </div>
    <div v-if="characterLimit && editor.storage.characterCount">
      <p
        class="text-sm text-gray-300"
        :class="{
          'text-yellow-500':
            editor.storage.characterCount.characters() >= 0.97 * characterLimit &&
            !(editor.storage.characterCount.characters() === characterLimit),
          'text-red-500': editor.storage.characterCount.characters() === characterLimit,
        }"
      >
        {{ Math.max(editor.storage.characterCount.characters(), 0) }}/{{ characterLimit }}
      </p>
    </div>
  </div>
</template>

<script>
import TextMenuButton from './EditorMenuButton.vue';
import BlockquoteIcon from '../custom_icons/BlockquoteIcon.vue';
import BulletedListIcon from '../custom_icons/BulletedListIcon.vue';
import OrderedListIcon from '../custom_icons/OrderedListIcon.vue';

export default {
  props: ['editor', 'characterLimit'],
  components: {
    TextMenuButton,
    BlockquoteIcon,
    BulletedListIcon,
    OrderedListIcon,
  },
};
</script>
