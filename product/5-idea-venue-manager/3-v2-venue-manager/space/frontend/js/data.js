/* ============================================================
   DATA — mock store for the venue-ops console
   ============================================================ */
const Data = {
  org: { dateLabel: '', timeLabel: '', channel: 'WhatsApp' },

  stats: { pending: 9, confirmedToday: 12, occupancy: 0, occupancyWeek: 0 },

  slots: [],
  bookings: [],

  venues: [
    { id: 'north',  name: 'North Field',  slot: '8 AM – 12 PM', surface: 'Grass',  type: 'Natural',   suggested: 6000 },
    { id: 'south',  name: 'South Field',  slot: '8 AM – 12 PM', surface: 'Turf',   type: 'Synthetic', suggested: 5500 },
    { id: 'indoor', name: 'Indoor Arena', slot: '8 AM – 12 PM', surface: 'Matting',type: 'Indoor',    suggested: 7200 },
  ],

  requests: [
    { id: 'r1', name: 'Aman Sharma',   players: 12, type: 'Corporate', ago: '1 min ago',  day: 'Tomorrow', slot: '8 AM – 12 PM', phone: '+91 98765 43210', activity: 'Cricket', date: 'Tomorrow, 25 May 2025', isNew: true },
    { id: 'r2', name: 'Rohit Verma',   players: 10, type: 'Friends',   ago: '3 min ago',  day: 'Tomorrow', slot: '2 PM – 6 PM',  phone: '+91 99820 11223', activity: 'Cricket', date: 'Tomorrow, 25 May 2025', isNew: true },
    { id: 'r3', name: 'Karan Mehta',   players: 14, type: 'League',    ago: '5 min ago',  day: 'Tomorrow', slot: '8 AM – 12 PM', phone: '+91 98191 55667', activity: 'Cricket', date: 'Tomorrow, 25 May 2025', isNew: true },
    { id: 'r4', name: 'Vikas Singh',   players: 12, type: 'Corporate', ago: '7 min ago',  day: 'Today',    slot: '2 PM – 6 PM',  phone: '+91 90011 22334', activity: 'Cricket', date: 'Today, 24 May 2025',    isNew: true },
    { id: 'r5', name: 'Neha Iyer',     players: 8,  type: 'Friends',   ago: '9 min ago',  day: 'Tomorrow', slot: '2 PM – 6 PM',  phone: '+91 98330 44556', activity: 'Cricket', date: 'Tomorrow, 25 May 2025', isNew: true },
    { id: 'r6', name: 'Arjun Nair',    players: 16, type: 'League',    ago: '12 min ago', day: 'Tomorrow', slot: '8 AM – 12 PM', phone: '+91 97400 66778', activity: 'Cricket', date: 'Tomorrow, 25 May 2025', isNew: true },
    { id: 'r7', name: 'Siddharth Rao', players: 11, type: 'Friends',   ago: '15 min ago', day: 'Tomorrow', slot: '2 PM – 6 PM',  phone: '+91 96500 88990', activity: 'Cricket', date: 'Tomorrow, 25 May 2025', isNew: true },
  ],

  integrations: [
    { id: 'telecast', name: 'Video Telecast', icon: 'video', s1: 'Disabled',      s2: 'Unavailable' },
    { id: 'cricheroes', name: 'CricHeroes',   icon: 'cric',  s1: 'Not Connected', s2: 'Disabled' },
  ],
};
