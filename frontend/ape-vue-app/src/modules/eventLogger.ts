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
import options from './options';
import { getUserToken } from './serverUtil';
import IdleTimer from '@/modules/IdleTimer';

import { store } from '@/store';

enum EventLogType {
  IdleEvent = 'IdleEvent',
  Idle1min = 'Idle1min',
  Idle3min = 'Idle3min',
  Idle5min = 'Idle5min',
  ActiveEvent = 'ActiveEvent',
  AcceptEvent = 'AcceptEvent',
  RejectEvent = 'RejectEvent',
  CopyEvent = 'CopyEvent',
  UndoEvent = 'UndoEvent',
  RedoEvent = 'RedoEvent',
}

type EventPostBody = {
  event: string,
  userEmail: string | null | undefined,
  timestamp: string,
}

class EventLogger {
  static eventRoute = '/events';

  static onIdle = (idleThresholdSeconds: number) => {
    switch (idleThresholdSeconds) {
      case 60 * 5: {
        return EventLogger.log(EventLogType.Idle5min);
      }
      case 60 * 3: {
        return EventLogger.log(EventLogType.Idle3min);
      }
      case 60: {
        return EventLogger.log(EventLogType.Idle1min);
      }
      default: {
        return null;
      }
    }
  };

  static onActive = () => {
    EventLogger.log(EventLogType.ActiveEvent);
  };

  static idleTimer = new IdleTimer(EventLogger.onIdle, EventLogger.onActive);

  static async log(event: EventLogType) {
    if (!store.state.user) {
      console.debug('user is not defined');
      return;
    }

    if (options.useFakeApi) {
      // eslint-disable-next-line no-console
      console.debug(`Skipped logging event of type: ${event} for user: ${store.state.user?.email} because fake API is being used`);
      return;
    }

    const userToken: string = await getUserToken(store.state.user);

    const postBody: EventPostBody = {
      event,
      userEmail: store.state.user?.email,
      timestamp: new Date().toUTCString(),
    };

    const response = await fetch(`${options.baseUrlApi}${EventLogger.eventRoute}`, {
      method: 'POST',
      headers: {
        Accept: '*/*',
        'Content-Type': 'application/json',
        Authorization: `Bearer ${userToken}`,
      },
      body: JSON.stringify(postBody),
    });

    if (!response.ok) {
      throw Error(response.statusText);
    }
  }
}

export { EventLogger, EventLogType };
