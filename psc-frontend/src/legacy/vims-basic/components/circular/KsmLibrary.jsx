// src/components/dashboardlayout/KsmLibrary.jsx
import React, { useState, useEffect, useRef } from "react";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import {
  AlertTriangle,
  FileText,
  FileSearch,
  Bell,
  BellRing,
  CheckCircle2,
  User,
  Mail,
  FileDown,
  Eye,
  X,
  Trash2
} from "lucide-react";
import { useNavigate } from "react-router-dom";

function fixDate(dateString) {
  if (!dateString) return null;
  return new Date(dateString.replace(" ", "T").split(".")[0]);
}

const REMINDER_STORAGE_KEY = "circular-master-reminded-crews";

const getTypeIcon = (type) => {
  if (type === "Alert") return <AlertTriangle className="h-3 w-3" />;
  if (type === "Circular") return <FileText className="h-3 w-3" />;
  if (type === "Work Instruction") return <CheckCircle2 className="h-3 w-3" />;
  return null;
};

const getTypeVariant = (type) => "outline";

const normalizeNotificationTitle = (item) => {
  const titleCandidates = [
    item?.title,
    item?.notification_title,
    item?.notificationTitle,
    item?.subject,
  ];

  for (const candidate of titleCandidates) {
    if (typeof candidate !== "string") continue;
    const normalizedTitle = candidate.replace(/\r\n|\n/g, " ").trim();
    if (normalizedTitle) {
      return normalizedTitle;
    }
  }

  return "No title";
};

const normalizeHashtags = (value) => {
  if (Array.isArray(value)) {
    return value
      .map((tag) => String(tag || "").trim())
      .filter(Boolean);
  }

  if (typeof value === "string") {
    return value
      .split(/[\s,]+/)
      .map((tag) => tag.trim())
      .filter(Boolean);
  }

  return [];
};

const KsmLibrary = ({
  user,
  // Permission props
  canViewList,
  canViewDetail,
  canAcknowledge,
  canViewCrewStatus,
  canRemindCrew,
  canDownloadPdf,
  canAccessPdf,
  onViewPdf,

  // Filter props from Dashboard.jsx
  searchTerm,
  scope,
  selectedTypes,
  selectedCriticalities,
  onlyUnread,
}) => {
  const detailsPanelRef = useRef(null);
  const navigate = useNavigate();
  
  const [selectedId, setSelectedId] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Crew list state
  const [showCrewList, setShowCrewList] = useState(false);
  const [crewList, setCrewList] = useState([]);
  const [crewLoading, setCrewLoading] = useState(false);
  const [sendingCrewReminder, setSendingCrewReminder] = useState(null);
  const [expandedTitle, setExpandedTitle] = useState(null);
  const [remindedCrewByNotification, setRemindedCrewByNotification] = useState(() => {
    if (typeof window === "undefined") return {};
    try {
      const storedValue = window.localStorage.getItem(REMINDER_STORAGE_KEY);
      return storedValue ? JSON.parse(storedValue) : {};
    } catch (error) {
      console.error("Failed to read reminder state from storage:", error);
      return {};
    }
  });

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(REMINDER_STORAGE_KEY, JSON.stringify(remindedCrewByNotification));
    } catch (error) {
      console.error("Failed to persist reminder state:", error);
    }
  }, [remindedCrewByNotification]);

  const openTitleModal = (title) => {
    const normalizedTitle = String(title || "").trim();
    if (!normalizedTitle) return;
    setExpandedTitle(normalizedTitle);
  };

  const closeTitleModal = () => {
    setExpandedTitle(null);
  };

  // 📥 Fetch notifications
  useEffect(() => {
    if (!canViewList || !user) {
      setLoading(false);
      return;
    }

    const fetchNotifications = async () => {
    try {
      // ✅ DETERMINE ENDPOINT BASED ON ROLE
      const normalizedRole = (user.role || '').toLowerCase().trim();
      const isMaster = normalizedRole === 'master';
      console.log('User role:', user.role, 'Normalized:', normalizedRole, 'isMaster:', isMaster);

      const endpoint = isMaster
        ? 'http://localhost:8000/api/circular/api/ship/notifications/'
        : 'http://localhost:8000/api/circular/api/crew/notifications/';
      const crewId = user.crew_id || user.username;
      console.log('Fetching from:', endpoint);
      console.log("✅ Fetching notifications from:", endpoint, "with crew_id:", crewId);
      const res = await fetch(`${endpoint}?crew_id=${encodeURIComponent(crewId)}`);

      if (!res.ok) {
        const errorText = await res.text();
        console.error('Notification API error:', res.status, errorText);
        throw new Error(`Failed to load notifications (HTTP ${res.status})`);
      }

      const rawData = await res.json();
      if (!Array.isArray(rawData)) throw new Error('Invalid response format');

      const mapped = rawData.map(item => {
        const scopeLabel = item.scope || 'Other';
        const hashtags = normalizeHashtags(item.hashtags);
        const reminderSentAt = item.reminder_sent_at || null;
        const seenAt = item.seen_at || null;
        const isReminded = !seenAt && (Boolean(reminderSentAt) || Number(item.isReminded) === 1) ? 1 : 0;

        return {
          id: item.sr_no || 'N/A',
          title: normalizeNotificationTitle(item),
          type: item.type || 'Alert',
          criticality: item.criticality || 'Medium',
          hashtags,
          publishedDate: item.publishedDate ? item.publishedDate.replace("T", " ").split(".")[0] : "—",
          scope: scopeLabel,
          attachment_url: item.attachment_url || null,
          isReminded,
          isAck: item.isAck || 0,
          unreadCount: item.unreadCount || 0,
          totalCrew: item.totalCrew || 0,
          delivered_at: item.delivered_at || null,
          seen_at: seenAt,
          reminder_sent_at: reminderSentAt,
        };
      });

      const sorted = mapped.sort((a, b) => {
        if (a.isReminded !== b.isReminded) return b.isReminded - a.isReminded;
        if (a.isReminded === 1 && b.isReminded === 1) {
          return fixDate(b.reminder_sent_at) - fixDate(a.reminder_sent_at);
        }
        if (a.isAck !== b.isAck) return a.isAck - b.isAck;
        return fixDate(b.delivered_at) - fixDate(a.delivered_at);
      });

      setNotifications(sorted);
    } catch (err) {
      console.error('Fetch error:', err);
      setError(err.message || 'Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  fetchNotifications();
}, [user, canViewList]);

  // 👥 Fetch crew list
  useEffect(() => {
    if (!showCrewList || !canViewCrewStatus || !selectedId) return;

    const fetchCrewList = async () => {
      setCrewLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/api/circular/api/crew/list/?notification_id=${selectedId}&crew_id=${user.crew_id || user.username}`);
        if (!res.ok) throw new Error('Failed to load crew status');
        const data = await res.json();
        const localReminderState = remindedCrewByNotification[selectedId] || {};
        const normalizedCrewList = data.map((crew) => ({
            ...crew,
            reminder_sent_at: crew.reminder_sent_at || localReminderState[crew.crew_id] || null,
          }));

        const acknowledgedCrewIds = normalizedCrewList
          .filter((crew) => crew.status === "Acknowledged")
          .map((crew) => crew.crew_id);

        if (acknowledgedCrewIds.length > 0) {
          setRemindedCrewByNotification((prev) => {
            const existingState = prev[selectedId];
            if (!existingState) return prev;

            const nextNotificationState = { ...existingState };
            acknowledgedCrewIds.forEach((crewId) => {
              delete nextNotificationState[crewId];
            });

            if (Object.keys(nextNotificationState).length === Object.keys(existingState).length) {
              return prev;
            }

            if (Object.keys(nextNotificationState).length === 0) {
              const { [selectedId]: _removed, ...rest } = prev;
              return rest;
            }

            return {
              ...prev,
              [selectedId]: nextNotificationState,
            };
          });
        }

        setCrewList(normalizedCrewList);
      } catch (err) {
        console.error('Fetch crew error:', err);
        alert('Failed to load crew list');
      } finally {
        setCrewLoading(false);
      }
    };

    fetchCrewList();
  }, [showCrewList, selectedId, canViewCrewStatus, user, remindedCrewByNotification]);

  useEffect(() => {
    setCrewList([]);
    setShowCrewList(false);
    setSendingCrewReminder(null);
  }, [selectedId]);

  // 🛎️ Remind crew
  const handleRemindIndividualCrew = async (employeeId) => {
    if (!canRemindCrew) return;
    if (sendingCrewReminder) return;
    
    setSendingCrewReminder(employeeId);

    try {
      const res = await fetch('http://localhost:8000/api/circular/api/msc/remind-crew/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          msc_sr_no: selectedId,
          master_id: user.crew_id || user.username,
          crew_id: employeeId, 
        }),
      });
      
      if (res.ok) {
        alert(`Reminder sent to ${employeeId}`);
        const reminderTimestamp = new Date().toISOString();

        setRemindedCrewByNotification((prev) => ({
          ...prev,
          [selectedId]: {
            ...(prev[selectedId] || {}),
            [employeeId]: reminderTimestamp,
          },
        }));

        setCrewList((prev) =>
          prev.map((crew) =>
            crew.crew_id === employeeId
              ? { ...crew, reminder_sent_at: reminderTimestamp }
              : crew
          )
        );
      } else {
        const errorData = await res.json();
        alert('Failed: ' + (errorData.error || 'Unknown error'));
      }
    } catch (err) {
      console.error('Remind error:', err);
      alert('Network error');
    } finally {
      setSendingCrewReminder(null);
    }
  };

  // ✅ Acknowledge notification
  const handleAcknowledge = async (notification) => {
    if (!canAcknowledge) return;
    
    try {
      const res = await fetch('http://localhost:8000/api/circular/api/msc/read-ack/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          notification_id: notification.id,
          crew_id: user.crew_id || user.username
        }),
      });

      if (res.ok) {
        setNotifications(prev =>
          prev.map(n => n.id === notification.id ? { ...n, isAck: 1 } : n)
        );
      }
    } catch (err) {
      console.error('Acknowledge failed:', err);
      alert('Failed to acknowledge notification.');
    }
  };

  const handleDownloadNotification = async (notification) => {
    if (!canDownloadPdf) return;

    try {
      const crewId = user?.crew_id || user?.username;
      const res = await fetch(
        `http://localhost:8000/api/circular/api/msc/pdf-url/?notificationId=${encodeURIComponent(notification.id)}&crew_id=${encodeURIComponent(crewId)}`
      );

      if (!res.ok) {
        throw new Error('Download not available');
      }

      const data = await res.json();
      const fileUrl = data.pdf_url || data.attachment_url;

      if (!fileUrl) {
        throw new Error('No file URL found');
      }

      const link = document.createElement('a');
      link.href = fileUrl;
      link.download = `MSC-${notification.id}.pdf`;
      link.click();
    } catch (err) {
      console.error('Download failed:', err);
      alert('Failed to download file.');
    }
  };

  // 🔍 Filter notifications - ONLY DECLARATION
  const filteredNotifications = notifications.filter((n) => {
    const matchesSearch =
      n.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      n.hashtags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesType = selectedTypes.includes(n.type);
    const matchesCriticality = selectedCriticalities.includes(n.criticality);
    const matchesScope = scope.includes(n.scope);
    const matchesUnread = !onlyUnread || n.isAck === 0;
    return matchesSearch && matchesType && matchesCriticality && matchesScope && matchesUnread;
  });

  const selectedNotification = notifications.find((n) => n.id === selectedId);
  const crewSummary = selectedNotification
    ? crewList.length > 0
      ? {
          total: crewList.length,
          read: crewList.filter((crew) => crew.status === 'Acknowledged').length,
        }
      : {
          total: selectedNotification.totalCrew || 0,
          read: Math.max(0, (selectedNotification.totalCrew || 0) - (selectedNotification.unreadCount || 0)),
        }
    : { total: 0, read: 0 };

  // 🖼️ Render helpers
  const getStatusColor = (isAck) => isAck ? 'border-blue-400' : 'border-red-400';
  const getCritColor = (criticality) => {
    switch (criticality) {
      case "Critical": return "bg-rose-50 text-rose-700 border-rose-200";
      case "High": return "bg-amber-50 text-amber-700 border-amber-200";
      case "Medium": return "bg-sky-50 text-sky-700 border-sky-200";
      default: return "bg-emerald-50 text-emerald-700 border-emerald-200";
    }
  };

  // Scroll to detail panel
  useEffect(() => {
    if (selectedId && detailsPanelRef.current) {
      const scroll = () => {
        if (detailsPanelRef.current) {
          const rect = detailsPanelRef.current.getBoundingClientRect();
          const isVisible = rect.top >= 0 && rect.bottom <= window.innerHeight;
          if (!isVisible) {
            const elementTop = rect.top + window.scrollY;
            const extraOffset = 80;
            window.scrollTo({ top: elementTop - extraOffset, behavior: 'smooth' });
          }
        }
      };
      const timer = setTimeout(() => requestAnimationFrame(scroll), 50);
      return () => clearTimeout(timer);
    }
  }, [selectedId]);

  if (!canViewList) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-center">
        <p className="text-yellow-800">You don't have access to view notifications.</p>
      </div>
    );
  }

  const showDetailPanel = canViewDetail && Boolean(selectedNotification);

  return (
    <div className="grid grid-cols-12 gap-6">
      {/* Left List Panel */}
      <div className={`col-span-12 ${showDetailPanel ? 'lg:col-span-7' : 'lg:col-span-12'}`}>
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="text-lg font-semibold text-neutral-800">KSM Library</h2>
          <div className="text-xs text-neutral-500">
            {loading ? 'Loading...' : `${filteredNotifications.length} results`}
          </div>
        </div>

        {loading ? (
          <div className="rounded-lg border border-dashed border-neutral-200 bg-white p-6 text-center text-sm text-neutral-500">Loading notifications...</div>
        ) : error ? (
          <div className="rounded-lg border border-error-100 bg-error-50 p-6 text-center text-sm text-error-700">{error}</div>
        ) : filteredNotifications.length === 0 ? (
          <div className="rounded-lg border border-dashed border-neutral-200 bg-white p-6 text-center text-sm text-neutral-500">No notifications match your filters</div>
        ) : (
          <div className="space-y-3">
            {filteredNotifications.map((notification) => (
              <Card
                key={notification.id}
                className={`cursor-pointer border-l-4 border-l-error-500 transition-shadow hover:shadow-md ${
                  selectedId === notification.id
                    ? 'border-primary-200 bg-primary-50/40'
                    : notification.isReminded === 1
                    ? 'border-warning-100 bg-warning-50/30'
                    : ''
                }`}
                onClick={() => {
                  setSelectedId(selectedId === notification.id ? null : notification.id);
                }}
              >
                <CardContent className="p-4">
                  <div className="mb-3 flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="font-medium text-neutral-900">{notification.id || "—"}</div>
                    </div>
                    <div className="flex items-center gap-1.5">
                      {canViewDetail && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-9 w-9 rounded-full border-neutral-200 bg-white p-0 hover:border-neutral-300 hover:bg-neutral-50"
                          onClick={(event) => {
                            event.stopPropagation();
                            setSelectedId(selectedId === notification.id ? null : notification.id);
                          }}
                          aria-label={`Open details for ${notification.title}`}
                          title="Open details"
                        >
                          <FileSearch className="h-4 w-4" />
                        </Button>
                      )}

                      {canAccessPdf && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-9 w-9 rounded-full border-neutral-200 bg-white p-0 hover:border-neutral-300 hover:bg-neutral-50"
                          onClick={(event) => {
                            event.stopPropagation();
                            onViewPdf(notification);
                          }}
                          aria-label={`View ${notification.title}`}
                          title="View"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      )}

                      {canDownloadPdf && (
                        <button
                          type="button"
                          onClick={(event) => {
                            event.stopPropagation();
                            handleDownloadNotification(notification);
                          }}
                          className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-neutral-200 bg-white text-neutral-700 shadow-sm transition-colors hover:border-neutral-300 hover:bg-neutral-50"
                          aria-label={`Download ${notification.title}`}
                          title="Download"
                        >
                          <FileDown className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="mb-3 flex items-start gap-3">
                    <div className="mt-0.5 flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-primary-100 bg-primary-50 text-primary-700 shadow-sm">
                      {getTypeIcon(notification.type) || <FileText className="h-4 w-4" />}
                    </div>
                    <div className="min-w-0 flex-1">
                      <button
                        type="button"
                        onClick={(event) => {
                          event.stopPropagation();
                          openTitleModal(notification.title);
                        }}
                        className="block w-full truncate text-left text-[17px] font-semibold leading-7 text-neutral-900 hover:text-primary-700"
                        title="Click to view full title"
                      >
                        {notification.title}
                      </button>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    <span className={`inline-flex items-center rounded-full px-3 py-1 text-[11px] font-semibold shadow-sm ${notification.isAck === 0 ? "bg-error-50 text-error-700" : "bg-success-50 text-success-700"}`}>
                      {notification.isAck === 0 ? "Unread" : "Read"}
                    </span>
                    {notification.isReminded === 1 && (
                      <span className="inline-flex items-center gap-1 rounded-full bg-warning-50 px-2.5 py-1 text-[11px] font-semibold text-warning-700 shadow-sm">
                        <BellRing className="h-3 w-3" />
                        Reminded
                      </span>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Detail Panel */}
      {showDetailPanel && (
        <div ref={detailsPanelRef} className="col-span-12 lg:col-span-5">
          <Card className="shadow-md">
            <CardContent className="p-4 space-y-3">
              {selectedNotification ? (
                <>
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-2">
                        <button
                          type="button"
                          onClick={() => openTitleModal(selectedNotification.title)}
                          className="truncate text-left text-base font-semibold text-neutral-800 hover:text-primary-700"
                          title="Click to view full title"
                        >
                          {selectedNotification.title}
                        </button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 shrink-0"
                          onClick={() => {
                            setSelectedId(null);
                            setShowCrewList(false);
                          }}
                          aria-label="Close details"
                          title="Close"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                      <div className="mt-2 flex gap-2">
                        <Badge
                          variant={getTypeVariant(selectedNotification.type)}
                          className="flex items-center justify-start gap-1 border-primary-200 bg-primary-50 text-primary-700 text-xs"
                        >
                          {getTypeIcon(selectedNotification.type)}
                          {selectedNotification.type}
                        </Badge>
                        <Badge
                          className={`flex items-center justify-center gap-1 border px-2 py-0.5 text-xs font-medium ${
                            selectedNotification.criticality === "Critical"
                              ? "border-error-100 bg-error-50 text-error-700"
                              : selectedNotification.criticality === "High"
                              ? "border-warning-100 bg-warning-50 text-warning-700"
                              : "border-primary-200 bg-primary-50 text-primary-700"
                          }`}
                        >
                          {selectedNotification.criticality}
                        </Badge>
                        {selectedNotification.isReminded === 1 && (
                          <Badge className="border-warning-100 bg-warning-50 text-warning-700 text-xs">
                            <BellRing className="h-3 w-3" />
                            Reminded
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-1 text-xs text-neutral-600">
                    <div><span className="font-semibold">ID:</span> {selectedNotification.id}</div>
                    <div><span className="font-semibold">Published:</span> {selectedNotification.publishedDate}</div>
                    <div><span className="font-semibold">Scope:</span> {selectedNotification.scope}</div>
                    {selectedNotification.reminder_sent_at && (
                      <div>
                        <span className="font-semibold">Reminded at:</span>{" "}
                        {new Date(selectedNotification.reminder_sent_at).toLocaleString()}
                      </div>
                    )}
                    <div className="flex items-center gap-2 flex-wrap mt-1">
                      {selectedNotification.hashtags.length > 0 && (
                        <Badge
                          variant="outline"
                          className="border-primary-200 bg-primary-50 text-primary-700 text-xs"
                        >
                          {selectedNotification.hashtags.join(' ')}
                        </Badge>
                      )}
                      
                      {selectedNotification.attachment_url && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="gap-2 border-neutral-300 p-2 text-xs"
                          onClick={(e) => {
                            e.stopPropagation();
                            onViewPdf(selectedNotification);
                          }}
                        >
                          <FileDown className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* Crew Status Panel */}
                  {canViewCrewStatus && (
                    <div className="border-t border-neutral-200 pt-3">
                      <div className="grid grid-cols-1 gap-3 text-xs">
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <div className="text-[11px] text-neutral-500">Read</div>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-auto p-0 text-xs font-medium text-primary-700 hover:bg-transparent"
                              onClick={() => setShowCrewList(!showCrewList)}
                            >
                              {showCrewList ? 'Hide Crew' : 'View Crew Status'}
                            </Button>
                          </div>
                          <div className="mt-1 h-2 overflow-hidden rounded-full bg-neutral-200">
                            <div
                              className="h-full rounded-full bg-primary-500"
                              style={{ width: `${crewSummary.total > 0 ? Math.round((crewSummary.read / crewSummary.total) * 100) : 0}%` }}
                            />
                          </div>
                          <div className="mt-1 flex justify-between">
                            <span>{crewSummary.read}/{crewSummary.total}</span>
                          </div>
                        </div>
                      </div>

                      {showCrewList && (
                        <div className="border-t border-neutral-200 pt-4">
                          <h4 className="font-medium text-sm mb-2">Crew Members</h4>
                          {crewLoading ? (
                            <p className="text-xs text-neutral-500">Loading crew list...</p>
                          ) : crewList.length === 0 ? (
                            <p className="text-xs text-neutral-500">No crew members found.</p>
                          ) : (
                            <div className="space-y-2 max-h-60 overflow-y-auto">
                              {crewList.map((crew) => (
                                <div
                                  key={crew.crew_id}
                                  className={`flex items-center justify-between p-2 rounded-md ${
                                    crew.status === 'Acknowledged'  
                                      ? 'bg-green-50 border border-green-200'
                                      : 'bg-red-50 border border-red-200'
                                  }`}
                                >
                                  <div className="flex items-center gap-2">
                                    <User className={`h-4 w-4 ${crew.status === 'Acknowledged' ? 'text-green-600' : 'text-red-600'}`} />
                                    <span className="text-xs font-medium">{crew.name || crew.crew_id}</span>
                                  </div>
                                  <div className="flex items-center gap-1">
                                    <Mail className={`h-3 w-3 ${crew.status === 'Acknowledged' ? 'text-green-600' : 'text-red-600'}`} />
                                    <span className={`text-xs ${crew.status === 'Acknowledged' ? 'text-green-600' : 'text-red-600'}`}>
                                      {crew.status === 'Acknowledged' ? 'Read' : 'Unread'}
                                    </span>
                                  </div>

                                  {canRemindCrew && crew.status !== 'Acknowledged' && (
                                    crew.reminder_sent_at ? (
                                      <div className="ml-2 flex flex-col items-end gap-1">
                                        <div
                                          className="inline-flex items-center gap-1 rounded-full bg-warning-50 px-2 py-1 text-xs font-medium text-warning-700"
                                          title={`Reminder already sent to ${crew.crew_id}`}
                                        >
                                          <BellRing className="h-3.5 w-3.5" />
                                          Reminded
                                        </div>
                                        <div className="text-[11px] text-warning-700">
                                          {new Date(crew.reminder_sent_at).toLocaleString()}
                                        </div>
                                      </div>
                                    ) : (
                                      <button
                                        type="button"
                                        disabled={sendingCrewReminder === crew.crew_id}
                                        className="inline-flex items-center gap-1 rounded-full border border-red-400 px-2 py-0.5 text-xs text-red-700 transition hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-60"
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleRemindIndividualCrew(crew.crew_id);
                                        }}
                                      >
                                        <Bell className={`h-4 w-4 mr-1 ${sendingCrewReminder === crew.crew_id ? 'animate-pulse' : ''}`} />
                                        {sendingCrewReminder === crew.crew_id ? 'Sending...' : 'Remind'}
                                      </button>
                                    )
                                  )}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </>
              ) : (
                <p className="py-8 text-center text-neutral-500">
                  {loading ? 'Loading...' : 'Select a notification to see details'}
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {expandedTitle && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={closeTitleModal}>
          <div className="w-full max-w-2xl rounded-xl bg-white shadow-xl" onClick={(event) => event.stopPropagation()}>
            <div className="flex items-center justify-between border-b border-neutral-200 px-6 py-4">
              <h2 className="text-lg font-semibold text-neutral-900">Full Title</h2>
              <button
                type="button"
                onClick={closeTitleModal}
                className="rounded-md p-1 text-gray-500 transition hover:bg-neutral-100 hover:text-gray-700"
                aria-label="Close full title modal"
              >
                &times;
              </button>
            </div>
            <div className="px-6 py-5 text-sm leading-7 text-neutral-800 break-words">
              {expandedTitle}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KsmLibrary;
