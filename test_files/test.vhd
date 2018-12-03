
library ieee;
use ieee.std_logic_1164.all;
use ieee.std_logic_misc.all;
use ieee.numeric_std.all;

entity debounce is
	generic(
		freq			: integer := 100000000;
    debounce_time : integer := 10000000		--In terms of NS
	);
	port(
		clk			: in std_logic;
		resetn		: in std_logic;
		
		signal_in	: in std_logic;
		signal_out	: out std_logic
	);
end debounce;

architecture debounce_a of debounce is
  --------------------------------------------------
  -- This is an line comment
  --constant ns 		: integer := 1_000_000_000/freq;
	constant ns 		: integer := 1_000_000_000/freq;  -- Comment

	constant count 		: integer := debounce_time / ns; --Comment
	--Comment

	signal ff			: std_logic_vector( 1 downto 0 );  --Comment
	signal last_in		: std_logic; -- This is another comment
	signal counter 		: integer range 0 to count;--Comment
	signal counter_reset: std_logic; 
begin
	
	counter_reset	<= xor_reduce(ff);
	
	signal_out		<= last_in;
	
	counter_p : process( clk )
	begin
		if rising_edge( clk ) then
			if resetn = '0' then
				counter		<= 0;
				last_in		<= '0';
			else 
				if counter_reset = '1' then
					counter	<= 0;
				elsif counter /= count then
					counter	<= counter + 1;
				else
					last_in	<= ff( 1 ); 
				end if;
			end if;
		end if;
	end process;
	
	ff_p : process( clk )
	begin
		if rising_edge( clk ) then
			if resetn = '0' then
				ff		<= ( others => '0' );
			else 
				ff( 0 )	<= signal_in;
				ff( 1 ) <= ff( 0 );
			end if;
		end if;
	end process;
end debounce_a;

--synthesis translate_off
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity debounce_ut is
end debounce_ut;

architecture debounce_ut_a of debounce_ut is

	signal i_clk	: std_logic	:= '0';
	signal i_resetn	: std_logic	:= '0';
	signal i_in	: std_logic;
	signal i_out	: std_logic;
begin
	UUT : entity work.debounce
		generic map(
			freq		=> 100000000,
			debounce_time => 10000000
		)
		port map
		(
			clk			=> i_clk,
			resetn		=> i_resetn,
			signal_in	=> i_in,
			signal_out	=> i_out
		);
	
	i_clk		<= not i_clk after 5ns;
	i_resetn	<= '0', '1' after 100ns;
	
	process
	begin
		i_in	<= '0';
		wait until rising_edge( i_clk ) and i_resetn = '1';
		
		wait for 100ns;
		
		i_in	<= '1';
		
		wait for 1ms;
		
		for i in 0 to 10 loop
			i_in	<= '0';
			wait for 1ms;
			i_in	<= '1';
			wait for 1ms;
		end loop;
		
		wait for 40ms;
		
		i_in	<= '0';
		
		wait for 5ms;
		
		for i in 0 to 10 loop
			i_in	<= '1';
			wait for 1ms;
			i_in	<= '0';
			wait for 1ms;
		end loop;
		
		i_in	<= '1';
		
		wait for 5ms;
		
		i_in	<= '0';
		
		
		wait;
	end process;
end debounce_ut_a;
--synthesis translate_on