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
import { getDeepCopyOfObject, posMod } from './otherUtil';

interface HistoryManager<A> {
  maxLength: number;
  pos: number;
  start: number;
  end: number;
  states: A[];
  deepCopy: boolean;
  lastReturnedState: A | null;
}

class HistoryManager<A> {
  constructor(maxLength = 10, deepCopy = true) {
    this.maxLength = maxLength;
    this.deepCopy = deepCopy;
    this.clear();
  }

  /**
   * Reset to initial state.
   */
  clear() {
    this.pos = 0;
    this.start = 0;
    this.end = 0;
    this.states = [];
    this.lastReturnedState = null;
  }

  /**
   * Checks whether it is possible to go one step back in the history.
   */
  canGoBack() {
    if (
      // Currently in oldest state
      this.pos === this.start
      // History is empty
      || this.states.length === 0
    ) {
      return false;
    }

    return true;
  }

  /**
   * Goes back one step in the history
   * @returns Whether the operation was successful.
   */
  goBack() {
    if (!this.canGoBack()) {
      return false;
    }

    this.pos = posMod(this.pos - 1, this.maxLength);
    return true;
  }

  /**
   * Checks whether it's possible to go one step forward in the history.
   * @returns Whether it's possible to go one step forward
   */
  canGoForward() {
    if (
      // Currently in newest state
      this.pos === this.end
      // History is empty
      || this.states.length === 0
    ) {
      return false;
    }

    return true;
  }

  /**
   * Goes one step forward in the history.
   * @returns Whether the operation was successful.
   */
  goForward() {
    if (!this.canGoForward()) {
      return false;
    }

    this.pos = posMod(this.pos + 1, this.maxLength);
    return true;
  }

  /**
   * Adds a new state to the history and moves the current position to that state.
   * @param state The state to be added to the history.
   * @returns True if successful, false if unsuccessful. It is unsuccessful if it is a
   * duplicate state.
   */
  addToHistory(state: A) {
    // Abort if the new state is already the current state
    if (
      this.getState()
      && JSON.stringify(this.getState()) === JSON.stringify(state)
    ) {
      return false;
    }

    if (this.states.length !== 0) {
      this.end = posMod(this.pos + 1, this.maxLength);
      this.pos = this.end;

      if (this.start === this.end) {
        this.start = posMod(this.end + 1, this.maxLength);
      }
    }

    this.states[this.pos] = this.deepCopy ? getDeepCopyOfObject(state) : state;
    return true;
  }

  /**
   * Gets the state at the current position
   * @returns the state at the current position (or null if the history is empty).
   */
  getState() {
    if (this.states.length === 0) {
      // History is empty
      return null;
    }

    const result = this.states[this.pos];

    return this.deepCopy ? getDeepCopyOfObject(result) : result;
  }
}

export default HistoryManager;
