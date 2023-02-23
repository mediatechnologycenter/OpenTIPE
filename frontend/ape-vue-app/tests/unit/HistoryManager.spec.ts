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
import HistoryManager from '@/modules/HistoryManager';

describe(HistoryManager, () => {
  it('Handles adding items', () => {
    const hm = new HistoryManager<number>(10, false);

    const itemsToAdd = [1, 2, 3];

    itemsToAdd.forEach((item) => {
      hm.addToHistory(item);
    });

    itemsToAdd.forEach((item) => {
      expect(hm.states.includes(item)).toBeTruthy();
    });
  });

  it('Returns the correct state', () => {
    const hm = new HistoryManager<number>(10, false);

    const itemsToAdd = [1, 2, 3];

    itemsToAdd.forEach((item) => {
      hm.addToHistory(item);
      expect(hm.getState()).toBe(item);
    });
  });

  it('Handles going back and forward', () => {
    const hm = new HistoryManager<number>(3, false);

    const itemsToAdd = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];

    let stateIndex = -1;
    function getCurrent() {
      return itemsToAdd[stateIndex];
    }

    for (let i = 0; i < 3; i += 1) {
      stateIndex += 1;
      hm.addToHistory(getCurrent());
    }

    expect(hm.getState()).toBe(getCurrent());
    expect(hm.canGoBack()).toBeTruthy();

    stateIndex -= 1;
    hm.goBack();

    expect(hm.getState()).toBe(getCurrent());

    for (let i = 0; i < 5; i += 1) {
      stateIndex += 1;
      hm.addToHistory(getCurrent());
    }

    expect(hm.getState()).toBe(getCurrent());

    for (let i = 0; i < 2; i += 1) {
      stateIndex -= 1;
      hm.goBack();
    }

    expect(hm.getState()).toBe(getCurrent());

    for (let i = 0; i < 2; i += 1) {
      stateIndex += 1;
      hm.goForward();
    }

    expect(hm.getState()).toBe(getCurrent());
  });

  it('Handles more states than maxLength', () => {
    const hm = new HistoryManager<number>(3, false);

    hm.addToHistory(1);
    hm.addToHistory(2);
    hm.addToHistory(3);
    hm.addToHistory(4);

    expect(hm.states).toEqual([4, 2, 3]);
  });

  it('Handles going back and adding something', () => {
    const hm = new HistoryManager<number>(3, false);

    hm.addToHistory(1);
    hm.addToHistory(2);
    hm.addToHistory(3);
    hm.addToHistory(4);

    hm.goBack();
    hm.goBack();

    hm.addToHistory(5);
    expect(hm.canGoForward()).toBeFalsy();
    expect(hm.states).toEqual([4, 2, 5]);
  });

  it('Cannot go back or forward too far', () => {
    const hm = new HistoryManager<number>(3, false);

    hm.addToHistory(1);
    hm.addToHistory(2);
    hm.addToHistory(3);
    hm.addToHistory(4);

    hm.goBack();
    hm.goBack();
    expect(hm.canGoBack()).toBeFalsy();

    hm.goForward();
    hm.goForward();
    expect(hm.canGoForward()).toBeFalsy();
  });

  test('Random testing', () => {
    const size = 3;
    const hm = new HistoryManager<number>(size, false);

    const refHistory = [0];
    hm.addToHistory(0);
    let nextElement = 1;
    let index = 0;
    let newestStateIndex = 0;
    let canGoBack = 0;

    for (let i = 0; i < 5000; i += 1) {
      const x = Math.random();

      /**
       * Randomly do one of the following actions: add, go back, go forward
       */
      if (x < 0.333) {
        // Add something
        index += 1;
        refHistory[index] = nextElement;
        hm.addToHistory(nextElement);
        nextElement += 1;
        newestStateIndex = index;

        expect(hm.canGoForward()).toBeFalsy();
        expect(hm.canGoBack()).toBeTruthy();
        canGoBack = Math.min(canGoBack + 1, size - 1);
      } else if (x < 0.666) {
        // Go forward

        if (newestStateIndex <= index) {
          // Currently in "newest" position
          expect(hm.canGoForward()).toBeFalsy();
          expect(hm.goForward()).toBeFalsy();
        } else {
          // Has newer state
          index += 1;
          canGoBack = Math.min(canGoBack + 1, size - 1);
          expect(hm.canGoForward()).toBeTruthy();
          expect(hm.goForward()).toBeTruthy();
        }
      } else if (!canGoBack) {
        // Can't go back
        expect(hm.canGoBack()).toBeFalsy();
        expect(hm.goBack()).toBeFalsy();
      } else {
        // Go back
        index -= 1;
        canGoBack = Math.min(canGoBack - 1, size - 1);
        expect(hm.canGoBack()).toBeTruthy();
        expect(hm.goBack()).toBeTruthy();
      }
      expect(hm.getState()).toEqual(refHistory[index]);
    }
  });
});
