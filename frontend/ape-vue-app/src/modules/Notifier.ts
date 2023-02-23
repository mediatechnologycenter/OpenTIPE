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
import { InjectionKey } from 'vue';
import { NotificationMessageType } from './types';

interface NotifyOptions {
  automaticallyDismissAfter?: number;
  messageType: NotificationMessageType;
}

type NotifyFunction = (msg: string, options: NotifyOptions) => void;

class Notifier {
  private notifyFunctions: NotifyFunction[] = [];

  private dismissFunctions: (() => void)[] = [];

  private currentNotificationId: string = '';

  private notificationQueue: { message: string; options: NotifyOptions }[] = [];

  private displayNotification(message: string, options: NotifyOptions) {
    const localNotificationId = String(Date.now());
    this.currentNotificationId = localNotificationId;
    // Display this notification
    this.notifyFunctions.forEach((f) => f(message, options));

    // Dismiss it automatically if necessary
    if (options.automaticallyDismissAfter) {
      setTimeout(() => {
        if (this.currentNotificationId !== localNotificationId) {
          return;
        }
        this.dismissCurrentNotification();
      }, options.automaticallyDismissAfter);
    }
  }

  notify(message: string, options: NotifyOptions) {
    // Add new notification to the queue
    this.notificationQueue.push({ message, options });

    // Already busy
    if (this.notificationQueue.length > 1) {
      return;
    }

    this.displayNotification(message, options);
  }

  dismissCurrentNotification() {
    if (this.notificationQueue.length === 0) {
      return;
    }

    this.dismissFunctions.forEach((f) => f());

    setTimeout(() => {
      // Remove old notification from queue
      this.notificationQueue.shift();
      const newNotification = this.notificationQueue.find(
        (x) => x !== undefined,
      );

      if (newNotification) {
        this.displayNotification(
          newNotification.message,
          newNotification.options,
        );
      }
    }, 300);
  }

  onNewNotification(f: NotifyFunction) {
    this.notifyFunctions.push(f);
  }

  onDismissNotification(f: () => void) {
    this.dismissFunctions.push(f);
  }
}

const notifierKey: InjectionKey<Notifier> = Symbol('store');

export { notifierKey, Notifier };
