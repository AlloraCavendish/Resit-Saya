// Purpose: Custom hook for synchronized server clock ticking every second in server timezone.
// Security: Safe local clock ticker; relies on single initial server synchronization without persistent polling.

import { useEffect, useState } from "react";
import { getServerTime } from "../api/meta";

export function useServerClock() {
  const [clockState, setClockState] = useState({
    timeStr: "--:--:--",
    dateStr: "---",
    timezone: "Asia/Kuala_Lumpur",
    synced: false,
  });

  useEffect(() => {
    let offsetMs = 0;
    let tz = "Asia/Kuala_Lumpur";
    let timerId = null;

    const syncClock = async () => {
      try {
        const data = await getServerTime();
        tz = data.timezone || "Asia/Kuala_Lumpur";
        const serverEpoch = new Date(data.current_time).getTime();
        offsetMs = serverEpoch - Date.now();
      } catch {
        // Fallback to local time if offline
      }

      const updateTicker = () => {
        const nowServerMs = Date.now() + offsetMs;
        const nowServerDate = new Date(nowServerMs);

        try {
          const timeFormatted = nowServerDate.toLocaleTimeString("en-MY", {
            timeZone: tz,
            hour12: false,
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          });

          const dateFormatted = nowServerDate.toLocaleDateString("en-MY", {
            timeZone: tz,
            weekday: "short",
            day: "numeric",
            month: "short",
            year: "numeric",
          });

          setClockState({
            timeStr: timeFormatted,
            dateStr: dateFormatted,
            timezone: tz,
            synced: true,
          });
        } catch {
          setClockState({
            timeStr: nowServerDate.toTimeString().split(" ")[0],
            dateStr: nowServerDate.toDateString(),
            timezone: tz,
            synced: true,
          });
        }
      };

      updateTicker();
      timerId = setInterval(updateTicker, 1000);
    };

    syncClock();

    return () => {
      if (timerId) clearInterval(timerId);
    };
  }, []);

  return clockState;
}
