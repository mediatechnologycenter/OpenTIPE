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
import scrollIntoView from 'smooth-scroll-into-view-if-needed';

function scrollToElementsWithClass(cssClass: string) {
  const elements = document.getElementsByClassName(cssClass);
  Array.from(elements).forEach(async (el) => {
    const isSuggestionCard = el.classList.contains('suggestion-card');
    await scrollIntoView(el, {
      behavior: 'smooth',
      scrollMode: isSuggestionCard ? 'always' : 'if-needed',
      block: isSuggestionCard ? 'start' : 'center',
    });
  });
}

export {
  // eslint-disable-next-line import/prefer-default-export
  scrollToElementsWithClass,
};
