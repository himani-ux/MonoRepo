// src/components/dashboardlayout/KsmLibrary.jsx
import React, { useState, useEffect, useRef } from "react";
import { Card, CardContent } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import {
  AlertTriangle,
  FileText,
  ChevronRight,
  Bell,
  CheckCircle2,
  User,
  Mail,
  FileDown,
  Eye,
  Trash2
} from "lucide-react";
import { useNavigate } from "react-router-dom";

function fixDate(dateString) {
  if (!dateString) return null;
  return new Date(dateString.replace(" ", "T").split(".")[0]);
}

const getTypeIcon = (type) => {
  if (type === "Alert") return <AlertTriangle className="h-3 w-3" />;
  if (type === "Circular") return <FileText className="h-3 w-3" />;
  if (type === "Work Instruction") return <CheckCircle2 className="h-3 w-3" />;
  return null;
};

const getTypeVariant = (type) => "outline";

const KsmLibrary = ({
  user,
  // Permission props
  canViewList,
  canViewDetail,
  canAcknowledge,
  canViewCrewStatus,
  canRemindCrew,
  canDownloadPdf,
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
        let hashtags = [];
        if (typeof item.hashtags === 'string') {
          hashtags = item.hashtags.split(',').map(h => h.trim()).filter(Boolean);
        } else if (Array.isArray(item.hashtags)) {
          hashtags = item.hashtags;
        }

        return {
          id: item.sr_no || 'N/A',
          title: item.title?.replace(/\r\n|\n/g, ' ') || 'No title',
          type: item.type || 'Alert',
          criticality: item.criticality || 'Medium',
          hashtags: Array.isArray(item.hashtags) ? item.hashtags : [],
          publishedDate: item.publishedDate ? item.publishedDate.replace("T", " ").split(".")[0] : "—",
          scope: scopeLabel,
          attachment_url: item.attachment_url || null,
          isReminded: item.isReminded || 0,
          isAck: item.isAck || 0,
          unreadCount: item.unreadCount || 0,
          totalCrew: item.totalCrew || 0,
          delivered_at: item.delivered_at || null,
          seen_at: item.seen_at || null,
          reminder_sent_at: item.reminder_sent_at || null,
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
        setCrewList(data);
      } catch (err) {
        console.error('Fetch crew error:', err);
        alert('Failed to load crew list');
      } finally {
        setCrewLoading(false);
      }
    };

    fetchCrewList();
  }, [showCrewList, selectedId, canViewCrewStatus, user]);

  // 🛎️ Remind crew
  const handleRemindIndividualCrew = async (employeeId) => {
    if (!canRemindCrew) return;
    
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
        setShowCrewList(false);
        setTimeout(() => setShowCrewList(true), 100);
      } else {
        const errorData = await res.json();
        alert('Failed: ' + (errorData.error || 'Unknown error'));
      }
    } catch (err) {
      console.error('Remind error:', err);
      alert('Network error');
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

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 grid grid-cols-12 gap-6 bg-sky-50">
      {/* Left List Panel */}
      <div className="col-span-12 lg:col-span-7">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold">KSM Library  Test</h2>
          <div className="text-xs text-slate-500">
            {loading ? 'Loading...' : `${filteredNotifications.length} results`}
          </div>
        </div>

        {loading ? (
          <p className="text-center py-4">Loading notifications...</p>
        ) : error ? (
          <p className="text-center py-4 text-red-600">{error}</p>
        ) : filteredNotifications.length === 0 ? (
          <p className="text-center py-4 text-slate-500">No notifications match your filters</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredNotifications.map((notification) => (
              <div
                key={notification.id}
                className={`bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-all p-4 cursor-pointer ${
                  selectedId === notification.id ? "ring-2 ring-sky-200" : ""
                } ${
                  notification.isAck === 0 ? "border-red-400" : "border-blue-500"
                }`}
                onClick={() => {
                  setSelectedId(selectedId === notification.id ? null : notification.id);
                }}
              >
                {/* Top Row: Date + Criticality */}
                <div className="flex items-center justify-between mb-2">
                  <div className="text-xs text-gray-500">
                    {notification.publishedDate
                      ? new Date(notification.publishedDate).toLocaleDateString()
                      : "—"}
                  </div>
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      notification.criticality === "Critical"
                        ? "bg-red-100 text-red-700"
                        : notification.criticality === "High"
                        ? "bg-orange-100 text-orange-700"
                        : notification.criticality === "Medium"
                        ? "bg-yellow-100 text-yellow-700"
                        : "bg-green-100 text-green-700"
                    }`}
                  >
                    {notification.criticality}
                  </span>
                </div>

                {/* Title */}
                <h3 className="text-lg font-semibold text-gray-800 mb-2 line-clamp-2">
                  {notification.title}
                  {notification.isReminded === 1 && (
                    <span className="ml-2 inline-flex items-center gap-1 text-xs font-medium bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full">
                      <Bell className="h-3 w-3" />
                      Reminded
                    </span>
                  )}
                </h3>

                {/* Type Badge + Hashtags */}
                <div className="flex flex-wrap items-center gap-2 mb-3">
                  {/* Type badge */}
                  <span
                    className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      notification.type === "Alert"
                        ? "bg-red-100 text-red-700"
                        : notification.type === "Circular"
                        ? "bg-blue-100 text-blue-700"
                        : notification.type === "Work Instruction"
                        ? "bg-amber-100 text-amber-700"
                        : "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {notification.type}
                  </span>

                  {/* Hashtags */}
                  {notification.hashtags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {notification.hashtags
                        .slice(0, 3)
                        .map((tag, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 text-xs font-medium rounded-full bg-gradient-to-r from-sky-100 via-sky-200 to-sky-100 text-sky-800 border border-sky-200"
                          >
                            #{tag}
                          </span>
                        ))}
                    </div>
                  )}
                </div>

                {/* Footer: ID, Dept, Read Status */}
                <div className="mt-2 text-xs text-gray-600 flex flex-wrap gap-x-2 gap-y-1">
                  <span>ID: {notification.id}</span>
                  <span>•</span>
                  <span>Dept: {notification.scope}</span>
                  {canViewCrewStatus && (
                    <>
                      <span>•</span>
                      <span>
                        Read:{" "}
                        <span className="font-medium">
                          {notification.totalCrew - notification.unreadCount}/{notification.totalCrew}
                        </span>
                      </span>
                    </>
                  )}
                </div>

                {/* NO ACTION ICONS — EVER */}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Detail Panel */}
      {canViewDetail && (
        <div ref={detailsPanelRef} className="col-span-12 lg:col-span-5">
          <Card className="shadow-none border border-sky-100 rounded-xl">
            <CardContent className="p-4 space-y-3">
              {selectedNotification ? (
                <>
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-semibold text-base truncate">
                      {selectedNotification.title}
                    </h3>
                    <div className="flex gap-2">
                      <Badge
                        variant={getTypeVariant(selectedNotification.type)}
                        className="flex items-center gap-1 justify-start border-[#87CEEB] text-[#1E89B3] bg-[#E9F6FB] rounded-full text-xs"
                      >
                        {getTypeIcon(selectedNotification.type)}
                        {selectedNotification.type}
                      </Badge>
                      <Badge
                        className={`flex items-center justify-center gap-1 font-medium border px-2 py-0.5 rounded-full text-xs ${
                          selectedNotification.criticality === "Critical"
                            ? "border-[#D45959] text-[#D45959] bg-[#FFE6EA]"
                            : selectedNotification.criticality === "High"
                            ? "border-orange-300 text-orange-500 bg-[#FFFFE6]"
                            : "border-[#1E89B3] text-[#1E89B3] bg-[#E9F6FB]"
                        }`}
                      >
                        {selectedNotification.criticality}
                      </Badge>
                    </div>
                  </div>

                  <div className="text-xs text-slate-600 space-y-1">
                    <div><span className="font-semibold">ID:</span> {selectedNotification.id}</div>
                    <div><span className="font-semibold">Published:</span> {selectedNotification.publishedDate}</div>
                    <div><span className="font-semibold">Scope:</span> {selectedNotification.scope}</div>
                    <div className="flex items-center gap-2 flex-wrap mt-1">
                      <Badge
                        variant="outline"
                        className="border-[#87CEEB] text-[#1E89B3] bg-[#E9F6FB] rounded-full text-xs"
                      >
                        {selectedNotification.hashtags.join(' ')}
                      </Badge>
                      
                      {selectedNotification.attachment_url && (
                        <Button
                          size="sm"
                          variant="outline"
                          className="gap-2 border-sky-200 text-xs p-2"
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
                    <div className="border-t border-sky-100 pt-3">
                      <div className="grid grid-cols-1 gap-3 text-xs">
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <div className="text-[11px] text-slate-500">Read</div>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="p-0 h-auto font-medium text-xs text-sky-700 hover:bg-sky-50"
                              onClick={() => setShowCrewList(!showCrewList)}
                            >
                              {showCrewList ? 'Hide Crew' : 'View Crew Status'}
                            </Button>
                          </div>
                          <div className="h-2 bg-gray-200 rounded-full mt-1 overflow-hidden">
                            <div
                              className="h-full bg-blue-500 rounded-full"
                              style={{ width: `${Math.round(((selectedNotification.totalCrew - selectedNotification.unreadCount) / selectedNotification.totalCrew) * 100)}%` }}
                            />
                          </div>
                          <div className="mt-1 flex justify-between">
                            <span>{selectedNotification.totalCrew - selectedNotification.unreadCount}/{selectedNotification.totalCrew}</span>
                          </div>
                        </div>
                      </div>

                      {showCrewList && (
                        <div className="pt-4 border-t border-sky-200">
                          <h4 className="font-medium text-sm mb-2">Crew Members</h4>
                          {crewLoading ? (
                            <p className="text-xs text-slate-500">Loading crew list...</p>
                          ) : crewList.length === 0 ? (
                            <p className="text-xs text-slate-500">No crew members found.</p>
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

                                  {canRemindCrew && (
                                    <Badge
                                      variant="outline"
                                      className="cursor-pointer flex items-center gap-1 px-2 py-0.5 text-xs border-red-400 text-red-700 hover:bg-red-100"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleRemindIndividualCrew(crew.crew_id);
                                      }}
                                    >
                                      <Bell className="h-4 w-4 mr-1" />
                                      Remind
                                    </Badge>
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
                <p className="text-muted-foreground text-center py-8">
                  {loading ? 'Loading...' : 'Select a notification to see details'}
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default KsmLibrary;