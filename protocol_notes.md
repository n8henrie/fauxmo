# protocol_notes.md

Details on the Echo's interaction with Fauxmo, and how to examine it for
debugging.

Tons of information gathered by @makermusings, I *strongly* recommend you start
by reading these:

- <https://github.com/makermusings/fauxmo/blob/master/protocol_notes.txt>
- <http://www.makermusings.com/2015/07/13/amazon-echo-and-home-automation>

In summary:

1. User tells Echo to "find connected devices" or clicks corresponding button
   in webapp
1. Echo broadcasts "device search" to `239.255.255.250:1900` (UDP)
1. Fauxmo response includes `LOCATION` of `setup.xml` endpoint for each
   "device" in config (UDP)
1. Echo requests `setup.xml` endpoint at above `LOCATION` (HTTP) for each
   device
1. Fauxmo responds with setup information for each device (HTTP)
1. Alexa verbally announces any discovered devices (*really* wish I could mute
   this -- set volume to 1 beforehand if I'll be doing it a bunch), and they
   also show up in the webapp

Once you understand the basic model of interaction, the next step in debugging
is to inspect the actual requests and responses.

The following commands require some tools you might not have by default; you
can get them with: `sudo apt-get install tcpdump tshark nmap`. Doesn't
matter what you choose regarding the wireshark question you'll get during
installation; just read the warning and make a good decision. On OSX, use
[homebrew](http://brew.sh) to install the same.

First, get the IP address of your Echo. If you don't know it:
```bash
# Assuming your local subnet is 192.168.27.*
sudo nmap -sP 192.168.27.1/24 | grep -i -B 2 F0:27:2D
```
You should get `Nmap scan report for 192.168.27.XXX` -- your Echo IP address.
For the examples below, I'll use `192.168.27.100` as the Echo IP address, and
`192.168.27.31` as the Pi's IP address (31 as in 3.14, easier to remember).

Next, we'll check out the info being sent to and from the Echo and Fauxmo. In
one window, run Fauxmo in verbose mode. In a second window, run the commands
below, and check their output when you tell the Echo to find connected devices.

To get an overview of what's going on, start with `tshark`:

```
sudo tshark -f "host 192.168.27.100" -Y "udp"

# Alternatively, only show the Echo's SEARCH requests:
sudo tshark -f "host 192.168.27.100" -Y "udp contains SEARCH"

# Only show the Fauxmo responses (note still using the Echo's IP):
sudo tshark -f "host 192.168.27.100" -Y "udp contains LOCATION"
```

Example output for the first command, showing a few sets of SSDP SEARCH sent by
the Echo followed by 4 responses by Fauxmo (1 for each device in sample
config).

```
Capturing on 'eth0'
  1   0.000000 192.168.27.100 -> 239.255.255.250 SSDP 149 M-SEARCH * HTTP/1.1
  2   0.046414 192.168.27.31 -> 192.168.27.100 SSDP 428 HTTP/1.1 200 OK
  3   0.064351 192.168.27.31 -> 192.168.27.100 SSDP 428 HTTP/1.1 200 OK
  4   0.082011 192.168.27.31 -> 192.168.27.100 SSDP 428 HTTP/1.1 200 OK
  5   0.101093 192.168.27.31 -> 192.168.27.100 SSDP 428 HTTP/1.1 200 OK
  6   0.104016 192.168.27.100 -> 239.255.255.250 SSDP 149 M-SEARCH * HTTP/1.1
  7   0.151414 192.168.27.31 -> 192.168.27.100 SSDP 428 HTTP/1.1 200 OK
  8   0.171049 192.168.27.31 -> 192.168.27.100 SSDP 428 HTTP/1.1 200 OK
  9   0.191602 192.168.27.31 -> 192.168.27.100 SSDP 428 HTTP/1.1 200 OK
 10   0.199882 192.168.27.31 -> 192.168.27.100 SSDP 428 HTTP/1.1 200 OK
 11   0.231841 192.168.27.100 -> 239.255.255.250 SSDP 164 M-SEARCH * HTTP/1.1
 12   0.333406 192.168.27.100 -> 239.255.255.250 SSDP 164 M-SEARCH * HTTP/1.1
```

To get a raw look at all the info, use `tcpdump`. I've cleaned up a bunch of
garbage in the below output, but you should still be able to recognize each of
the critical components.

```bash
sudo tcpdump -s 0 -i eth0 -A host 192.168.27.100
```

This should show a ton of detailed info, including all responses sent to / from
the Echo. Replace `etho` with your network interface (check with `ip link`) and
`192.168.27.100` with your Echo's IP address.

The output should start with several of the Echo's UDP based discovery
requests, where you can recognize the `UDP` protocol being sent from the Echo
`192.168.27.100` to the network's multicast broadcast `239.255.255.250.1900`,
something like:

```
15:48:39.268125 IP 192.168.27.100.50000 > 239.255.255.250.1900: UDP, length 122
M-SEARCH * HTTP/1.1
HOST: 239.255.255.250:1900
MAN: "ssdp:discover"
MX: 15
ST: urn:Belkin:device:**
```

Below that, you should see Fauxmo's responses, also UDP, one for each device in
the config. This response provides the Echo with the `LOCATION` of the device's
`setup.xml`.

```
15:48:39.513741 IP 192.168.27.31.1900 > 192.168.27.100.50000: UDP, length 386
HTTP/1.1 200 OK
CACHE-CONTROL: max-age=86400
DATE: Sun, 24 Apr 2016 21:48:39 GMT
EXT:
LOCATION: http://192.168.27.31:12340/setup.xml
OPT: "http://schemas.upnp.org/upnp/1/0/"; ns=01
01-NLS: c66d1ad0-707e-495e-a21a-1d640eed4547
SERVER: Unspecified, UPnP/1.0, Unspecified
ST: urn:Belkin:device:**
USN: uuid:Socket-1_0-2d4ac336-8683-3660-992a-d056b5382a8d::urn:Belkin:device:**
```

Somewhere below that, you'll see the Echo request each device's `setup.xml`
(based on the `LOCATION` from the prior step), this time TCP instead of UDP.

```
15:48:39.761878 IP 192.168.27.100.39720 > 192.168.27.31.12341: Flags [P.], seq 1:68, ack 1, win 274, options [nop,nop,TS val 619246756 ecr 140303456], length 67
GET /setup.xml HTTP/1.1
Host: 192.168.27.31:12341
Accept: */*
```

And somewhere below that, Fauxmo's setup response, for each device in the
config, also TCP:

```
15:48:39.808164 IP 192.168.27.31.12342 > 192.168.27.100.59999: Flags [P.], seq 1:608, ack 68, win 453, options [nop,nop,TS val 140303462 ecr 619246754], length 607
HTTP/1.1 200 OK
CONTENT-LENGTH: 375
CONTENT-TYPE: text/xml
DATE: Sun, 24 Apr 2016 21:48:39 GMT
LAST-MODIFIED: Sat, 01 Jan 2000 00:01:15 GMT
SERVER: Unspecified, UPnP/1.0, Unspecified
X-User-Agent: Fauxmo
CONNECTION: close

<?xml version="1.0"?>
<root>
<device>
<deviceType>urn:Fauxmo:device:controllee:1</deviceType>
<friendlyName>fake hass switch by REST API</friendlyName>
<manufacturer>Belkin International Inc.</manufacturer>
<modelName>Emulated Socket</modelName>
<modelNumber>3.1415</modelNumber>
<UDN>uuid:Socket-1_0-cbc4bc63-e0e2-3a78-8a9f-f0ff7e419b79</UDN>
</device>
</root>
```

Then, to get a *really* close look at a request, well go back to `tshark`. For
example, we can add the `-V` flag to get a **ton** more info, and add `-c 1`
(count) to limit to capturing a single packet, and further refine the capture
filter by specifying that we only want to look at packets sent **from** the Pi
**to** the Echo.

```bash
sudo tshark -f "src 192.168.27.31 and dst 192.168.27.100" -c 1 -V
```

At the bottom, you should find the `Hypertext Transfer Protocol` section
contains the same `setup.xml` response we found in the `tcpdump` output above.

You can also send requests from another device on the network to check out
Fauxmo's responses and ensure that they're getting through the network. For
example, to simulate the Echo's device search, run the following from another
device on the network, in two different windows:

```bash
# Seems to work with `nc.traditional` on Raspberry Pi, not yet working for me on OSX
# Window 1: Listen for response on port 12345 (should show up once second command is sent)
nc.traditional -l -u -p 12345

# Window 2: Send simulated UDP broadcast device search (from port 12345)
echo -e '"ssdp:discover"urn:Belkin:device:**' | nc.traditional -b -u -p 12345 239.255.255.250 1900
```

To request a device's `setup.xml`, using the device's `port` from `config.json`:

```bash
# Send a request for the `setup.xml` of a device from the sample config
curl -v 192.168.27.31:12340/setup.xml
```

The above commands may seem a little complicated if you're unfamiliar, but
they're immensely powerful and indispensable for debugging these tricky network
issues.  If you're not already familiar with them, learning the basics will
serve you well in your IoT endeavors!

To verify that Fauxmo is working properly, check for a few things:

1. Is the Pi consistently seeing the Echo's `M-SEARCH` requests?
2. Is Fauxmo consistently replying with the `LOCATION` responses?
3. Is the Echo then requesting the `setup.xml` (for each device)?
4. Is Fauxmo consistently replying with the setup info?

If you can confirm that things seem to be working through number 4, then it
would seem that Fauxmo is working properly, and the issue would seem to be
elsewhere.

## On and Off Commands

One way to examine exactly what the Echo sends to one of your connected Fauxmo
devices (i.e. one that *already* works as expected) is to first **stop** Fauxmo
(to free up the port), then use netcat to listen to that port while you trigger
the command. E.g. for a Fauxmo device configured to use port `12345`, run
`nc.traditional -l 12345` and then tell the Echo to "turn on [device name]".
The Echo will notify you that the command failed, obviously, because Fauxmo
isn't running, but you should be able to see exactly what the Echo sent.

These are the requests that the Echo sends to Fauxmo when you ask it to turn a
device...

### On

```
POST /upnp/control/basicevent1 HTTP/1.1
Host: 192.168.27.31:12345
Accept: */*
Content-type: text/xml; charset="utf-8"
SOAPACTION: "urn:Belkin:service:basicevent:1#SetBinaryState"
Content-Length: 299

<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body>
<u:SetBinaryState xmlns:u="urn:Belkin:service:basicevent:1">
<BinaryState>1</BinaryState>
</u:SetBinaryState>
</s:Body>
</s:Envelope>
```

### Off

```
POST /upnp/control/basicevent1 HTTP/1.1
Host: 192.168.27.31:12345
Accept: */*
Content-type: text/xml; charset="utf-8"
SOAPACTION: "urn:Belkin:service:basicevent:1#SetBinaryState"
Content-Length: 299

<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body>
<u:SetBinaryState xmlns:u="urn:Belkin:service:basicevent:1">
<BinaryState>0</BinaryState>
</u:SetBinaryState>
</s:Body>
</s:Envelope>
```

Several similar terms can be used instead of `On` and `Off`, e.g. `Open` and
`Close`; the response looks identical. [This Reddit
post](https://www.reddit.com/r/amazonecho/comments/4gaf05/discovery_a_lot_more_smart_home_action_phrases/)
has a good number more that work. NB: the `Dim` commands in the post don't seem
to work (likely incompatible with Wemo devices, so the Echo doesn't even try to
send them).

As of sometime around 20171030, it will also now send a `GetBinaryState`
action when viewing a device, which [can be
problematic](https://github.com/n8henrie/fauxmo/issues/31) for earlier versions
of Fauxmo (prior to v0.4.5).

```
POST /upnp/control/basicevent1 HTTP/1.1
Host: 192.168.27.31:12345
Accept: */*
Content-type: text/xml; charset="utf-8"
SOAPACTION: "urn:Belkin:service:basicevent:1#GetBinaryState"
Content-Length: 299

<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body>
<u:GetBinaryState xmlns:u="urn:Belkin:service:basicevent:1">
<BinaryState>1</BinaryState>
</u:GetBinaryState>
</s:Body>
</s:Envelope>
```

I think I have a good idea what the Fauxmo response should look like, thanks to
help from:

- [u/romanpet](https://www.reddit.com/r/homeautomation/comments/79wrl7/can_anybody_with_an_echo_a_wemo_and_wireshark/dp6akcc/)
- https://github.com/go-home-iot/belkin/blob/7b62ec854e9510f4857bb9eceeb8fef3d8b55fb4/device.go


```
POST /upnp/control/basicevent1 HTTP/1.1
Host: 192.168.27.31:12345
Accept: */*
Content-type: text/xml; charset="utf-8"
SOAPACTION: "urn:Belkin:service:basicevent:1#GetBinaryState"
Content-Length: 299

<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
<s:Body>
<u:GetBinaryStateResponse xmlns:u="urn:Belkin:service:basicevent:1">
<BinaryState>0</BinaryState>
</u:GetBinaryStateResponse>
</s:Body>
</s:Envelope>
```
