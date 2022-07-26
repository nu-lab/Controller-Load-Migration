#!/bin/bash
ethtool -K s3-eth1 tso off
ethtool -K s3-eth2 tso off

ethtool -K s4-eth1 tso off
ethtool -K s4-eth2 tso off
ethtool -K s4-eth3 tso off

ethtool -K s5-eth1 tso off
ethtool -K s5-eth2 tso off
ethtool -K s5-eth3 tso off