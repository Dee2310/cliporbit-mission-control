import { Office3DScene } from '/static/office3d.js';

const { createApp, ref, computed, onMounted, onUnmounted } = Vue;

createApp({
  setup() {
    const canvasContainer = ref(null);
    const cmdInputRef = ref(null);
    const activeView = ref('office');
    const rooms = ref({});
    const agents = ref({});
    const brain = ref({ notes_count: 0, recent_memories: [] });
    const tasks = ref([]);
    const selectedRoomId = ref(null);
    const selectedAgentId = ref(null);
    const commandTarget = ref('cliporbit');
    const commandInput = ref('');
    const roomTags = ref([]);
    const agentPills = ref([]);
    const lightingMode = ref('auto');
    const hqPin = ref(localStorage.getItem('agent_hq_pin') || '');
    const isDispatching = ref(false);
    const toast = ref({ visible: false, text: '', type: 'info', icon: '⚡' });

    let office3d = null;
    let animationFrameId = null;
    let ws = null;
    let isDragging = false;
    let prevX = 0;
    let initialPinchDist = null;
    let toastTimer = null;

    const showToast = (text, type = 'success', icon = '⚡') => {
      toast.value = { visible: true, text, type, icon };
      clearTimeout(toastTimer);
      toastTimer = setTimeout(() => {
        toast.value.visible = false;
      }, 4000);
    };

    const promptForPin = () => {
      const entered = window.prompt('Enter your Agent HQ 4-digit PIN:', hqPin.value);
      if (entered !== null && entered.trim()) {
        hqPin.value = entered.trim();
        localStorage.setItem('agent_hq_pin', hqPin.value);
        showToast('PIN saved on this device', 'success', '🔒');
        return true;
      }
      return false;
    };

    const authHeaders = () => ({
      'Content-Type': 'application/json',
      'X-HQ-PIN': hqPin.value
    });

    const selectedRoom = computed(() =>
      selectedRoomId.value ? rooms.value[selectedRoomId.value] : null
    );
    const selectedAgent = computed(() =>
      selectedAgentId.value ? agents.value[selectedAgentId.value] : null
    );

    const totalAgentCount = computed(() => Object.keys(agents.value).length);
    const runningAgentCount = computed(() =>
      Object.values(agents.value).filter((a) => a.state === 'working').length
    );

    const activeRooms = computed(() =>
      Object.values(rooms.value).filter((rm) =>
        Object.values(agents.value).some((a) => a.room === rm.id)
      )
    );

    const roomAgentsList = (roomId) =>
      Object.values(agents.value).filter((a) => a.room === roomId);

    const roomRunningCount = (roomId) =>
      Object.values(agents.value).filter((a) => a.room === roomId && a.state === 'working').length;

    const runningTasks = computed(() => tasks.value.filter((t) => t.status === 'running'));
    const waitingTasks = computed(() => tasks.value.filter((t) => t.status === 'waiting'));
    const doneTasks = computed(() => tasks.value.filter((t) => t.status === 'done'));

    const resolveMood = () => {
      if (lightingMode.value !== 'auto') return lightingMode.value;
      const hr = new Date().getHours();
      if (hr >= 6 && hr < 17) return 'day';
      if (hr >= 17 && hr < 20) return 'dusk';
      return 'night';
    };

    const lightingLabel = computed(() =>
      lightingMode.value === 'auto'
        ? `AUTO • ${resolveMood().toUpperCase()}`
        : lightingMode.value.toUpperCase()
    );

    const cycleLighting = () => {
      const order = ['auto', 'day', 'dusk', 'night'];
      lightingMode.value = order[(order.indexOf(lightingMode.value) + 1) % order.length];
      if (office3d) office3d.setLightingMood(resolveMood());
    };

    const clampRadius = (r) => Math.max(9, Math.min(46, r));
    const onWheel = (e) => {
      if (office3d) office3d.cameraRadius = clampRadius(office3d.cameraRadius + e.deltaY * 0.02);
    };
    const onPointerDown = (e) => { isDragging = true; prevX = e.clientX; };
    const onPointerMove = (e) => {
      if (!isDragging || !office3d) return;
      office3d.cameraAngle -= (e.clientX - prevX) * 0.006;
      prevX = e.clientX;
    };
    const onPointerUp = () => { isDragging = false; };

    const getTouchDist = (t1, t2) => Math.hypot(t1.clientX - t2.clientX, t1.clientY - t2.clientY);
    const onTouchStart = (e) => {
      if (e.touches.length === 1) {
        isDragging = true;
        prevX = e.touches[0].clientX;
        initialPinchDist = null;
      } else if (e.touches.length === 2) {
        isDragging = false;
        initialPinchDist = getTouchDist(e.touches[0], e.touches[1]);
      }
    };
    const onTouchMove = (e) => {
      if (!office3d) return;
      if (e.touches.length === 1 && isDragging) {
        office3d.cameraAngle -= (e.touches[0].clientX - prevX) * 0.008;
        prevX = e.touches[0].clientX;
      } else if (e.touches.length === 2 && initialPinchDist) {
        const d = getTouchDist(e.touches[0], e.touches[1]);
        office3d.cameraRadius = clampRadius(office3d.cameraRadius + (initialPinchDist - d) * 0.07);
        initialPinchDist = d;
      }
    };
    const onTouchEnd = () => { isDragging = false; initialPinchDist = null; };

    const selectRoom = (roomId) => {
      selectedAgentId.value = null;
      selectedRoomId.value = roomId;
      commandTarget.value = roomId;
      if (office3d) office3d.cameraRadius = 15.5;
    };

    const selectAgent = (agentId) => {
      selectedAgentId.value = agentId;
      const ag = agents.value[agentId];
      if (ag && ag.room) {
        selectedRoomId.value = ag.room;
        if (office3d) office3d.cameraRadius = 14.5;
      }
    };

    const focusCommandOnAgent = (ag) => {
      selectedAgentId.value = null;
      activeView.value = 'office';
      commandTarget.value = `agent:${ag.id}`;
      setTimeout(() => {
        if (cmdInputRef.value) cmdInputRef.value.focus();
      }, 100);
    };

    const clearFocus = () => {
      selectedRoomId.value = null;
      selectedAgentId.value = null;
      if (office3d) office3d.cameraRadius = 31;
    };

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      if (activeView.value !== 'office' || !office3d) return;
      office3d.renderFrame(Date.now(), selectedRoom.value, rooms.value, agents.value);
      const projected = office3d.projectLabels(rooms.value, agents.value);
      roomTags.value = projected.roomTags;
      agentPills.value = projected.agentPills;
    };

    const sendCommand = async () => {
      const text = commandInput.value.trim();
      if (!text) {
        showToast('Type an instruction for your agents first', 'error', '✍️');
        return;
      }

      isDispatching.value = true;
      try {
        let resp = await fetch('/api/command', {
          method: 'POST',
          headers: authHeaders(),
          body: JSON.stringify({ prompt: text, room: commandTarget.value })
        });

        if (resp.status === 403) {
          const ok = promptForPin();
          if (!ok) {
            showToast('PIN required to dispatch commands', 'error', '🔒');
            return;
          }
          resp = await fetch('/api/command', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ prompt: text, room: commandTarget.value })
          });
        }

        const data = await resp.json();
        if (!resp.ok) {
          showToast(data.error || 'Dispatch failed', 'error', '⚠️');
          return;
        }

        commandInput.value = '';
        showToast(data.message || 'Command dispatched!', data.triggered ? 'success' : 'info', '🚀');

        if (!commandTarget.value.startsWith('agent:')) {
          selectRoom(commandTarget.value);
        }
      } catch {
        showToast('Network error reaching Agent HQ', 'error', '📡');
      } finally {
        isDispatching.value = false;
      }
    };

    const spawnParallelSubagents = async (roomId) => {
      isDispatching.value = true;
      try {
        let resp = await fetch('/api/command', {
          method: 'POST',
          headers: authHeaders(),
          body: JSON.stringify({ prompt: 'Parallel batch execution', room: roomId })
        });
        if (resp.status === 403 && promptForPin()) {
          resp = await fetch('/api/command', {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify({ prompt: 'Parallel batch execution', room: roomId })
          });
        }
        const data = await resp.json();
        if (resp.ok) {
          showToast(data.message || 'Spawned 3 sub-agents', 'success', '⚡');
        } else {
          showToast(data.error || 'Unable to spawn', 'error', '🔒');
        }
      } finally {
        isDispatching.value = false;
      }
    };

    const approveTask = async (taskId) => {
      let resp = await fetch('/api/tasks/approve', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ task_id: taskId })
      });
      if (resp.status === 403 && promptForPin()) {
        resp = await fetch('/api/tasks/approve', {
          method: 'POST',
          headers: authHeaders(),
          body: JSON.stringify({ task_id: taskId })
        });
      }
      const data = await resp.json();
      if (resp.ok) {
        showToast(data.detail || 'Approved & dispatched!', 'success', '✅');
      } else {
        showToast(data.error || 'Approval failed', 'error', '🔒');
      }
    };

    const connectWebSocket = () => {
      const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      ws = new WebSocket(`${proto}//${window.location.host}/ws`);

      ws.onmessage = (event) => {
        let data;
        try { data = JSON.parse(event.data); } catch { return; }

        if (data.brain) brain.value = data.brain;
        if (data.tasks) tasks.value = data.tasks;

        if (data.type === 'INITIAL_STATE') {
          rooms.value = data.rooms;
          agents.value = data.agents;
          if (office3d) {
            Object.values(data.rooms).forEach((rm) => office3d.createRoom(rm));
            Object.values(data.agents).forEach((ag) => office3d.ensureAgent(ag, data.rooms));
          }
          return;
        }

        if (data.type === 'AGENT_UPDATE' && data.agent) {
          agents.value[data.agent.id] = { ...data.agent };
          if (office3d) office3d.ensureAgent(data.agent, rooms.value);
        }

        if (data.type === 'PARALLEL_SPAWN' && data.subagents) {
          for (const sub of data.subagents) {
            agents.value[sub.id] = sub;
            if (office3d) office3d.ensureAgent(sub, rooms.value);
          }
        }
      };

      ws.onclose = () => setTimeout(connectWebSocket, 3000);
    };

    const handleResize = () => { if (office3d) office3d.resize(); };

    onMounted(() => {
      office3d = new Office3DScene(canvasContainer.value);
      office3d.setLightingMood(resolveMood());
      animate();
      connectWebSocket();
      window.addEventListener('resize', handleResize);
    });

    onUnmounted(() => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      if (ws) ws.close();
    });

    return {
      canvasContainer, cmdInputRef, activeView, rooms, agents, brain, tasks,
      selectedRoomId, selectedRoom, selectedAgentId, selectedAgent,
      commandTarget, commandInput, roomTags, agentPills, lightingLabel,
      hqPin, promptForPin, isDispatching, toast,
      totalAgentCount, runningAgentCount, activeRooms,
      runningTasks, waitingTasks, doneTasks, roomAgentsList, roomRunningCount,
      cycleLighting, selectRoom, selectAgent, focusCommandOnAgent, clearFocus,
      sendCommand, spawnParallelSubagents, approveTask,
      onPointerDown, onPointerMove, onPointerUp, onWheel,
      onTouchStart, onTouchMove, onTouchEnd
    };
  }
}).mount('#app');