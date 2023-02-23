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
enum IdleStatus {
  idle = 'idle',
  active = 'active'
}

class IdleTimer {
  status: IdleStatus;

  private intervalId: number;

  private currentIntervalSeconds: number;

  constructor(private onIdle: Function, private onActive: Function, private idleTimeoutsSeconds = [60, 60 * 3, 60 * 5]) {
    this.status = IdleStatus.active;
    this.intervalId = this.reset();

    this.currentIntervalSeconds = 0;
  }

  /// Resets the timer and returns the new intervalId
  reset = () => {
    this.currentIntervalSeconds = 0;

    // Remove existing interval
    if (this.intervalId) {
      clearInterval(this.intervalId);
    }

    if (this.status === IdleStatus.idle) {
      this.status = IdleStatus.active;
      this.onActive();
    }

    // Updates the timer by one second every second & sets status to idle on expiration
    const intervalId = setInterval(() => {
      this.currentIntervalSeconds += 1;

      this.idleTimeoutsSeconds.forEach((threshold) => {
        if (this.currentIntervalSeconds === threshold) {
          this.status = IdleStatus.idle;
          this.onIdle(threshold);
        }
      });

      if (this.currentIntervalSeconds >= Math.max(...this.idleTimeoutsSeconds)) {
        clearInterval(intervalId);
      }
    }, 1000);

    this.intervalId = intervalId;
    return intervalId;
  };

  registerEventListeners = () => {
    document.addEventListener('click', this.reset);
    document.addEventListener('keydown', this.reset);
    document.addEventListener('wheel', this.reset);
    document.addEventListener('mousemove', this.reset); // This does not seem to work
  };

  removeEventListeners = () => {
    document.removeEventListener('click', this.reset);
    document.removeEventListener('keydown', this.reset);
    document.removeEventListener('wheel', this.reset);
    document.removeEventListener('mousemove', this.reset); // This does not seem to work
  };
}

export default IdleTimer;
